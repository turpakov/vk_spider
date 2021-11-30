import random
import time
#
import logging
import json
import re
#
from irequests import request
from .exceptions import *
from settings import Settings

log = logging.getLogger(__name__)

OPEN_ACC = 186101748
SLEEPING = 0.4


class VK:
    """ Модуль работы с VK """

    def __init__(self, settings):
        if type(settings) is not Settings:
            raise VkInvalidSettings
        self.API_VERSION = 5.101
        self.settings = settings
        self._TOKENS = []
        self._USED_TOKENS = []
        if settings.tokens_file_vk:
            self.load_tokens(settings.tokens_file_vk)
        self.check_tokens()

    def load_tokens(self, fname):
        self._TOKENS = list(map(str.strip, open(
            fname, "r", encoding=self.settings.encoding).readlines()))

    def check_tokens(self):
        for token in self._TOKENS:
            req_data = {
                "v": self.API_VERSION,
                "user_id": OPEN_ACC
            }
            try:
                self._vkapi_request("users.get", req_data, token)
            except VkInvalidToken:
                self._TOKENS.remove(token)

    def _vkapi_request(self, method: str, args: dict, token: str=None):
        """
        Make api requests to vk.com
        Arguments:
            method: str – method VkAPI
            args: dict – parameters for executed api-method
            token: str - token which use for request
        Return:
            result: dict – VkAPI response json
        """
        log.debug(f"Вызван VKAPI метод '{method}' с параметрами {args}")
        if token != None:
            req_data = {
                "access_token": token,
                "v": self.API_VERSION
            }
            if args:
                req_data.update(args)
        else:
            if self._TOKENS:
                token = random.choice(self._TOKENS)
                self._TOKENS.remove(token)
                self._USED_TOKENS.append(token)
            else:
                time.sleep(SLEEPING)
                self._TOKENS = self._USED_TOKENS
                self._USED_TOKENS = []
                token = random.choice(self._TOKENS)
            req_data = {
                "access_token": token,
                "v": self.API_VERSION
            }
            if args:
                req_data.update(args)
        data = request(f"https://api.vk.com/method/{method}", req_data, format_JSON=True)
        if "req_err" in data:
            log.error(f"VKApi request error! {data}")
        elif "error" in data:
            if data["error"]["error_code"] == 30:
                raise VkApiProfileIsPrivate
            elif data["error"]["error_code"] == 6:
                raise VkApiToManyExecute
            elif data["error"]["error_code"] == 9:
                raise VkApiTooManySameExecute
            elif data["error"]["error_code"] == 18:
                raise VkApiDeletedUser
            elif data["error"]["error_code"] == 37:
                raise VkApiBannedUser
            elif data["error"]["error_code"] == 29:
                raise VkApiLimitReached
            elif data["error"]["error_code"] == 5:
                raise VkInvalidToken
            elif data["error"]["error_code"] == 19:
                raise VkApiInaccessibleContent
            elif data["error"]["error_code"] == 204:
                raise VkApiNoAdmission
            elif data["error"]["error_code"] == 232:
                raise VkApiReactionCanNotBeApplied
            elif data["error"]["error_code"] == 212:
                raise VkApiNoAdmissionToComments
            elif data["error"]["error_code"] == 12:
                raise VkApiCompileError
            elif data["error"]["error_code"] == 13:
                raise VkApiDoingError
            else:
                raise BaseVkError
        elif "execute_errors" in data:
            if data["execute_errors"][0]["error_code"] == 30:
                raise VkApiProfileIsPrivate
            elif data["execute_errors"][0]["error_code"] == 6:
                raise VkApiToManyExecute
            elif data["execute_errors"][0]["error_code"] == 9:
                raise VkApiTooManySameExecute
            elif data["execute_errors"][0]["error_code"] == 18:
                raise VkApiDeletedUser
            elif data["execute_errors"][0]["error_code"] == 37:
                raise VkApiBannedUser
            elif data["execute_errors"][0]["error_code"] == 29:
                raise VkApiLimitReached
            elif data["execute_errors"][0]["error_code"] == 5:
                raise VkInvalidToken
            elif data["execute_errors"][0]["error_code"] == 19:
                raise VkApiInaccessibleContent
            elif data["execute_errors"][0]["error_code"] == 204:
                raise VkApiNoAdmission
            elif data["execute_errors"][0]["error_code"] == 232:
                raise VkApiReactionCanNotBeApplied
            elif data["execute_errors"][0]["error_code"] == 212:
                raise VkApiNoAdmissionToComments
            elif data["execute_errors"][0]["error_code"] == 12:
                raise VkApiCompileError
            elif data["execute_errors"][0]["error_code"] == 13:
                raise VkApiDoingError
            else:
                raise BaseVkError
        return data

    def result(self, status, data, errors):
        if errors:
            log.error(json.dumps(errors))
        return {
            "status": status,
            "error": errors,
            "result": data,
        }

    def get_friends(self, user_id: int, max_friends: int=10000):
        """
        Collect friends of user
        Arguments:
            user_id: int – id of user
            max_friends: int - num of returned friends
        Return:
            result: dict – {result: [users_id], error: {id: text_error, ...}, status: success or fail}
        """
        friends = []
        if max_friends < 5000:
            profiles_per_iteration = max_friends
        else:
            profiles_per_iteration = 5000
        code = f'var profiles_per_iteration={profiles_per_iteration};' \
               f'var user_id={user_id};' \
               f'var max_friends={max_friends};' \
               'var cur_offset=0;' \
               'var res=[];' \
               'var cur_iter=0;' \
               'while(cur_iter<25)' \
               '{' \
               'if (cur_offset>=max_friends)' \
               '{' \
               'return res;' \
               '}' \
               'var buff=API.friends.get({"user_id":user_id,' \
               '"offset":cur_offset,' \
               '"count":profiles_per_iteration});' \
               'if(buff.items.length<1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+profiles_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_friends = self._vkapi_request(
                "execute",
                {
                    "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{user_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{user_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{user_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{user_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{user_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{user_id: "29: Limit rate"}])
        except VkApiInaccessibleContent:
            return self.result("fail", None, [{user_id: "19: Inaccessible content"}])
        except VkApiNoAdmission:
            return self.result("fail", None, [{user_id: "204: No admission"}])
        except VkApiReactionCanNotBeApplied:
            return self.result("fail", None, [{user_id: "232: Reaction can not be applied to the object"}])
        except VkApiCompileError:
            return self.result("fail", None, [{user_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{user_id: "13: Code execution error"}])
        except VkInvalidToken:
            return self.result("fail", None, [{user_id: "5: Invalid token"}])
        except:
            return self.result("fail", None, [{user_id: "Unknown error"}])
        if "req_err" in res_friends:
            return self.result("fail", None, [{user_id: res_friends}])
        log.debug(f'user_id: {user_id}; ppi: {profiles_per_iteration} -> OK')
        if len(res_friends['response']) != 0:
            friends += res_friends['response']
        else:
            friends += res_friends['response']
        return self.result("success", friends, None)

    def get_followers(self, user_id: int, max_followers: int=25000):
        """
        Collect followers of user
        Arguments:
            user_id: int – id of user
            max_followers: int - num of returned followers
        Return:
            result: dict – {result: [users_id], error: {id: text_error, ...}, status: success or fail}
        """
        followers = []
        if max_followers < 1000:
            profiles_per_iteration = max_followers
        else:
            profiles_per_iteration = 1000
        code = f'var profiles_per_iteration={profiles_per_iteration};' \
               f'var user_id={user_id};' \
               f'var max_followers={max_followers};' \
               'var cur_offset=0;' \
               'var res=[];' \
               'var cur_iter=0;' \
               'while(cur_iter<25)' \
               '{' \
               'if(cur_offset>=max_followers)' \
               '{' \
               'return res;' \
               '}' \
               'var buff=API.users.getFollowers({"user_id":user_id,' \
               '"offset":cur_offset,' \
               '"count":profiles_per_iteration});' \
               'if(buff.items.length<1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+profiles_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_followers = self._vkapi_request(
                "execute",
                {
                   "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{user_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{user_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{user_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{user_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{user_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{user_id: "29: Limit rate"}])
        except VkApiCompileError:
            return self.result("fail", None, [{user_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{user_id: "13: Code execution error"}])
        except:
            return self.result("fail", None, [{user_id: "Unknown error"}])
        if "req_err" in res_followers:
            return self.result("fail", None, [{user_id: res_followers}])
        log.debug(f'user_id: {user_id}; ppi: {profiles_per_iteration} -> OK')
        if len(res_followers['response']) != 0:
            followers += res_followers['response']
        else:
            followers += res_followers['response']
        return self.result("success", followers, None)

    def get_friends_of_friends(self, user_id: int):
        """
        Collect friends of friends of user
        Arguments:
            user_id: int – id of user
        Return:
            result: dict – {result: {id: [friends], ...}, error: {id: text_error, ...}, status: success or fail}
        """
        fr_deep = {}
        friends = self.get_friends(user_id)
        if friends['result'] == None:
            return friends
        try:
            fr_deep["result"] = {}
            fr_deep["error"] = []
            for user in friends["result"]:
                fr_2 = self.get_friends(user)
                fr_deep["result"][user] = fr_2["result"]
                if fr_2["error"] != None:
                    fr_deep["error"].append(fr_2["error"][0])
            fr_deep["status"] = "success"
        except IndexError:
            fr_deep["status"] = "fail"
        return fr_deep

    def get_users(self, uids: list, fields: list=[]):
        """
            Collect information of users
            Arguments:
                uids: list – id of user
                fields: list - interested fields
            Return:
                result: dict – {result: [{"field": info, ...}], error: {id: text_error, ...}, status: success or fail}
        """
        uids_in_one_execute = 9 * 1000
        info = list()
        for start_index in range(0, len(uids), uids_in_one_execute):
            cur_uids = uids[start_index:start_index + uids_in_one_execute]
            fieldsForReq = ",".join(fields)
            code = f'var uids={cur_uids};' \
                   f'var fields_="{fieldsForReq}";' \
                   'var cur_pos=0;' \
                   'var info=[];' \
                   'while(cur_pos<uids.length)' \
                   '{' \
                   'var buff=API.users.get({"user_ids":uids.slice(cur_pos,cur_pos+1000),' \
                   '"fields":fields_});' \
                   'info=info+[buff];' \
                   'cur_pos=cur_pos+1000;' \
                   '}' \
                   'return info;'
            try:
                tmp_info = self._vkapi_request("execute", {"code": code})
            except VkApiToManyExecute:
                return self.result("fail", None, ["6: Too many executes"])
            except VkApiTooManySameExecute:
                return self.result("fail", None, ["9: Too many same actions"])
            except VkApiLimitReached:
                return self.result("fail", None, ["29: Limit rate"])
            except:
                return self.result("fail", None, ["Unknown error"])
            if "req_err" in tmp_info:
                return self.result("fail", None, [tmp_info])
            for part_info in tmp_info["response"]:
                info += part_info
        log.debug(f'user_id: {uids}; fields: {fields} -> OK')
        return self.result("success", info, None)

    def get_inst_of_user(self, user_id: int):
        """
        Collect instagram login of user
        Arguments:
            user_id: int – id of user
        Return:
            result: dict – {result: [{[user_id]: "instagram login"}], error: {id: text_error}, status: success or fail}
        """
        inst_log = {}
        link = self.get_users([user_id], ["connections", "status", "site"])
        if "instagram" in link['result'][0]:
            inst_log[user_id] = link['result'][0]["instagram"]
        if "status" in link['result'][0]:
            s = link['result'][0]['status'].lower()
            pattern = re.compile('inst')
            if s != '':
                if pattern.match(s) != None:
                    buff = link['result'][0]['status'].split(":")[1]
                    buff = buff.strip()
                    inst_log[user_id] = buff
        if "site" in link['result'][0]:
            pattern = re.compile('https://www.instagram.com/')
            if link['result'][0]['site'] != '':
                if pattern.match(link['result'][0]['site']) != None:
                    inst_log[user_id] = link['result'][0]['site'].split("/")[3]
        return self.result("success", [inst_log], None)

    def get_inst_of_user_friends(self, user_id: int):
        """
        Collect instagram logins of user friends
        Arguments:
            user_id: int – id of user
        Return:
            result: dict – {result: [{[user_id]: "instagram login", ...}], error: {id: text_error, ...},
            status: success or fail}
        """
        users = self.get_friends(user_id)
        if users['result'] == None:
            return users
        users = users['result']
        inst_logs = {}
        for user in users:
            link = self.get_users(user, ["connections", "status", "site"])
            if "instagram" in link['result'][0]:
                inst_logs[user] = link['result'][0]["instagram"]
                continue
            if "status" in link['result'][0]:
                s = link['result'][0]['status'].lower()
                pattern = re.compile('inst')
                if s != '':
                    if pattern.match(s) != None:
                        buff = link['result'][0]['status'].split(":")[1]
                        buff = buff.strip()
                        inst_logs[user] = buff
                        continue
            if "site" in link['result'][0]:
                pattern = re.compile('https://www.instagram.com/')
                if link['result'][0]['site'] != '':
                    if pattern.match(link['result'][0]['site']) != None:
                        inst_logs[user] = link['result'][0]['site'].split("/")[3]
        return self.result("success", [inst_logs], None)

    def get_groups(self, user_id: int, max_groups: int=5000):
        """
        Collect groups of user
        Arguments:
            user_id: int – id of user
            max_groups: int - num of returned groups
        Return:
            result: dict – {result: [groups_id], error: {id: text_error, ...}, status: success or fail}
        """
        groups = []
        if max_groups < 1000:
            groups_per_iteration = max_groups
        else:
            groups_per_iteration = 1000
        code = f'var groups_per_iteration={groups_per_iteration};' \
               f'var user_id={user_id};' \
               f'var max_groups={max_groups};' \
               'var cur_offset=0;' \
               'var res=[];' \
               'var cur_iter=0;' \
               'while(cur_iter<25)' \
               '{' \
               'if (cur_offset>=max_groups)' \
               '{' \
               'return res;' \
               '}' \
               'var buff=API.groups.get({"user_id":user_id,' \
               '"offset":cur_offset,' \
               '"count":groups_per_iteration});' \
               'if(buff.items.length<1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+groups_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_groups = self._vkapi_request(
                "execute",
                {
                    "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{user_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{user_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{user_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{user_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{user_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{user_id: "29: Limit rate"}])
        except VkApiLimitedListOfGroups:
            return self.result("fail", None, [{user_id: "260: Limited list of groups"}])
        except VkApiCompileError:
            return self.result("fail", None, [{user_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{user_id: "13: Code execution error"}])
        except:
            return self.result("fail", None, [{user_id: "Unknown error"}])
        if "req_err" in res_groups:
            return self.result("fail", None, [{user_id: res_groups}])
        log.debug(f'user_id: {user_id}; ppi: {groups_per_iteration} -> OK')
        if len(res_groups['response']) != 0:
            groups += res_groups['response']
        else:
            groups += res_groups['response']
        return self.result("success", groups, None)

    def get_group_members(self, group_id: int, first_offset: int = 0, max_members: int=1000000):
        """
        Collect members of group
        Arguments:
            group_id: int – id of group
            max_members: int - num of returned members
        Return:
            result: dict – {result: [members_ids], error: {id: text_error, ...}, status: success or fail}
        """
        cur_offset = first_offset
        group_id = -group_id
        members = []
        if max_members < 1000:
            members_per_iteration = max_members
        else:
            members_per_iteration = 1000
        code = f'var members_per_iteration={members_per_iteration};' \
               f'var group_id={group_id};' \
               f'var max_members={max_members};' \
               f'var cur_offset={cur_offset};' \
               'var res=[];' \
               'var cur_iter=0;' \
               'while(cur_iter<25)' \
               '{' \
               'if(cur_offset>=max_members)' \
               '{' \
               'return res;' \
               '}' \
               'var buff=API.groups.getMembers({"group_id":group_id,' \
               '"offset":cur_offset,' \
               '"count":members_per_iteration});' \
               'if(buff.items.length<1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+members_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_members = self._vkapi_request(
                "execute",
                {
                    "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{group_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{group_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{group_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{group_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{group_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{group_id: "29: Limit rate"}])
        except VkApiBadIdOfGroup:
            return self.result("fail", None, [{group_id: "125: Bad id of group"}])
        except VkApiLimitedListOfGroups:
            return self.result("fail", None, [{group_id: "260: Limited list of groups"}])
        except VkApiCompileError:
            return self.result("fail", None, [{group_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{group_id: "13: Code execution error"}])
        except:
            return self.result("fail", None, [{group_id: "Unknown error"}])
        if "req_err" in res_members:
            return self.result("fail", None, [{group_id: res_members}])
        log.debug(f'user_id: {group_id}; ppi: {members_per_iteration} -> OK')
        if len(res_members['response']) != 0:
            members += res_members['response']
        else:
            members += res_members['response']
        return self.result("success", members, None)

    def get_photos(self, owner_id: int, extended: int=0, max_photos: int=2000):
        """
        Collect photos of user or group
        Arguments:
            owner_id: int – id of user or group
            extended: int - extended information
            max_photos: int - num of returned photos
        Return:
            result: dict – {result: [{group id, photos info, ...}], error: {id: text_error, ...}, status: success or fail}
        """
        photos = []
        if max_photos < 200:
            photos_per_iteration = max_photos
        else:
            photos_per_iteration = 200
        code = f'var photos_per_iteration={photos_per_iteration};' \
               f'var owner_id={owner_id};' \
               f'var max_photos={max_photos};' \
               'var cur_offset=0;' \
               'var res=[];' \
               'var cur_iter=0;' \
               f'var extended={extended};' \
               'while(cur_iter<25)' \
               '{' \
               'if(cur_offset>=max_photos)' \
               '{' \
               'return res;' \
               '}' \
               'var buff=API.photos.getAll({"owner_id":owner_id,' \
               '"offset":cur_offset,' \
               '"extended":extended,' \
               '"count":photos_per_iteration});' \
               'if(buff.items.length<1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+photos_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_photos = self._vkapi_request(
                "execute",
                {
                    "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{owner_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{owner_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{owner_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{owner_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{owner_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{owner_id: "29: Limit rate"}])
        except VkApiInaccessibleContent:
            return self.result("fail", None, [{owner_id: "19: Inaccessible content"}])
        except VkApiCompileError:
            return self.result("fail", None, [{owner_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{owner_id: "13: Code execution error"}])
        except:
            return self.result("fail", None, [{owner_id: "Unknown error"}])
        if "req_err" in res_photos:
            return self.result("fail", None, [{owner_id: res_photos}])
        log.debug(f'group_id: {owner_id}; ppi: {photos_per_iteration} -> OK')
        if len(res_photos['response']) != 0:
            photos += res_photos['response']
        else:
            photos += res_photos['response']
        return self.result("success", photos, None)

    def get_videos(self, owner_id: int, extended: int=0, max_videos: int=1000):
        """
        Collect videos of user or group
        Arguments:
            owner_id: int – id of user or group
            extended: int - extended information
            max_photos: int - num of returned videos
        Return:
            result: dict – {result: [{user id, videos info, ...}], error: {id: text_error, ...}, status: success or fail}
        """
        videos = []
        if max_videos < 200:
            videos_per_iteration = max_videos
        else:
            videos_per_iteration = 200
        code = f'var videos_per_iteration={videos_per_iteration};' \
               f'var owner_id={owner_id};' \
               f'var max_videos={max_videos};' \
               'var cur_offset=0;' \
               'var res=[];' \
               'var cur_iter=0;' \
               f'var extended={extended};' \
               'while(cur_iter<25)' \
               '{' \
               'if(cur_offset>=max_videos)' \
               '{' \
               'return res;' \
               '}' \
               'var buff=API.video.get({"owner_id":owner_id,' \
               '"offset":cur_offset,' \
               '"extended":extended,' \
               '"count":videos_per_iteration});' \
               'if (buff.items.length < 1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+videos_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_videos = self._vkapi_request(
                "execute",
                {
                    "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{owner_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{owner_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{owner_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{owner_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{owner_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{owner_id: "29: Limit rate"}])
        except VkApiInaccessibleContent:
            return self.result("fail", None, [{owner_id: "19: Inaccessible content"}])
        except VkApiNoAdmission:
            return self.result("fail", None, [{owner_id: "204: No admission"}])
        except VkApiCompileError:
            return self.result("fail", None, [{owner_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{owner_id: "13: Code execution error"}])
        except:
            return self.result("fail", None, [{owner_id: "Unknown error"}])
        if "req_err" in res_videos:
            return self.result("fail", None, [{owner_id: res_videos}])
        log.debug(f'user_id: {owner_id}; ppi: {videos_per_iteration} -> OK')
        if len(res_videos['response']) != 0:
            videos += res_videos['response']
        else:
            videos += res_videos['response']
        return self.result("success", videos, None)

    def get_wall(self, owner_id: int, extended: int=0, max_notes: int = 1000):
        """
        Collect wall notes of user or group
        Arguments:
            owner_id: int – id of user or group
            extended: int - extended information
            max_photos: int - num of returned wall notes
        Return:
            result: dict – {result: [{group id, wall notes info, ...}], error: {id: text_error, ...}, status: success or fail}
        """
        notes = []
        if max_notes < 100:
            notes_per_iteration = max_notes
        else:
            notes_per_iteration = 100
        code = f'var notes_per_iteration={notes_per_iteration};' \
               f'var owner_id={owner_id};' \
               f'var max_notes={max_notes};' \
               'var cur_offset=0;' \
               'var res=[];' \
               'var cur_iter=0;' \
               f'var extended={extended};' \
               'while(cur_iter<25)' \
               '{' \
               'if(cur_offset>=max_notes)' \
               '{' \
               'return res;' \
               '}' \
               'var buff=API.wall.get({"owner_id":owner_id,' \
               '"offset":cur_offset,' \
               '"extended":extended,' \
               '"count":notes_per_iteration});' \
               'if(buff.items.length<1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+notes_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_notes = self._vkapi_request(
                "execute",
                {
                    "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{owner_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{owner_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{owner_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{owner_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{owner_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{owner_id: "29: Limit rate"}])
        except VkApiInaccessibleContent:
            return self.result("fail", None, [{owner_id: "19: Inaccessible content"}])
        except VkApiCompileError:
            return self.result("fail", None, [{owner_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{owner_id: "13: Code execution error"}])
        except:
            return self.result("fail", None, [{owner_id: "Unknown error"}])
        if "req_err" in res_notes:
            return self.result("fail", None, [{owner_id: res_notes}])
        log.debug(f'group_id: {owner_id}; ppi: {notes_per_iteration} -> OK')
        if len(res_notes['response']) != 0:
            notes += res_notes['response']
        else:
            notes += res_notes['response']
        return self.result("success", notes, None)

    def get_who_likes(self, type: str, owner_id: int, item_id: int, friends_only: int = 0, extended: int = 0,
                      max_likes: int = 10000000):
        """
        Collect likes of object
        Arguments:
            type:str - type of object(post, ...)
            owner_id: int – id of user or group
            item_id: int - id of object
            friends_only: int - указывает, необходимо ли возвращать только пользователей, которые являются друзьями текущего пользователя
            extended: int - extended information
            max_likes: int - max num of likes
        Return:
            result: dict – {result: [users_ids], error: {id: text_error, ...}, status: success or fail}
        """
        likes = []
        if max_likes < 1000:
            likes_per_iteration = max_likes
        else:
            likes_per_iteration = 1000
        code = f'var likes_per_iteration={likes_per_iteration};' \
               f'var owner_id={owner_id};' \
               f'var type="{type}";' \
               f'var item_id={item_id};' \
               f'var friends_only={friends_only};' \
               f'var max_likes={max_likes};' \
               'var cur_offset=0;' \
               'var res=[];' \
               'var cur_iter=0;' \
               f'var extended={extended};' \
               'while(cur_iter<25)' \
               '{' \
               'if(cur_offset>=max_likes)' \
               '{' \
               'return res;' \
               '}' \
               'var buff=API.likes.getList({"owner_id":owner_id,' \
               '"offset":cur_offset,' \
               '"type":type,' \
               '"item_id":item_id,' \
               '"friends_only":friends_only,' \
               '"extended":extended,' \
               '"count":likes_per_iteration});' \
               'if(buff.items.length<1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+likes_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_likes = self._vkapi_request(
                "execute",
                {
                    "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{owner_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{owner_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{owner_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{owner_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{owner_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{owner_id: "29: Limit rate"}])
        except VkApiInaccessibleContent:
            return self.result("fail", None, [{owner_id: "19: Inaccessible content"}])
        except VkApiNoAdmission:
            return self.result("fail", None, [{owner_id: "204: No admission"}])
        except VkApiReactionCanNotBeApplied:
            return self.result("fail", None, [{owner_id: "232: Reaction can not be applied to the object"}])
        except VkApiCompileError:
            return self.result("fail", None, [{owner_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{owner_id: "13: Code execution error"}])
        except:
            return self.result("fail", None, [{owner_id: "Unknown error"}])
        if "req_err" in res_likes:
            return self.result("fail", None, [{owner_id: res_likes}])
        log.debug(f'user_id: {owner_id}; ppi: {likes_per_iteration} -> OK')
        if len(res_likes['response']) != 0:
            likes += res_likes['response']
        else:
            likes += res_likes['response']
        return self.result("success", likes, None)

    def get_comments(self, owner_id: int, post_id: int, extended: int=0, max_comments: int=10000000):
        """
        Collect comments of post
        Arguments:
            owner_id: int – id of user or group
            post_id: int - id of object
            extended: int - extended information
            max_comments: int - max num of likes
        Return:
            result: dict – {result: [info...], error: {id: text_error, ...}, status: success or fail}
        """
        comments = []
        if max_comments < 100:
            comments_per_iteration = max_comments
        else:
            comments_per_iteration = 100
        code = f'var comments_per_iteration={comments_per_iteration};' \
               f'var owner_id={owner_id};' \
               f'var post_id={post_id};' \
               f'var max_comments={max_comments};' \
               'var cur_offset=0;' \
               'var res=[];' \
               'var cur_iter=0;' \
               f'var extended={extended};' \
               'while(cur_iter<25)' \
               '{' \
               'if(cur_offset>=max_comments)' \
               '{' \
               'return res;' \
               '}' \
               'var buff = API.wall.getComments({"owner_id":owner_id,' \
               '"post_id":post_id,' \
               '"need_likes":1,' \
               '"count":comments_per_iteration,' \
               '"offset":cur_offset,' \
               '"extended":extended});' \
               'if(buff.items.length<1)' \
               '{' \
               'return res;' \
               '}' \
               'res=res+buff.items;' \
               'cur_iter=cur_iter+1;' \
               'cur_offset=cur_offset+comments_per_iteration;' \
               '}' \
               'return res;'
        try:
            res_comments = self._vkapi_request(
                "execute",
                {
                    "code": code
                })
        except VkApiProfileIsPrivate:
            return self.result("fail", None, [{owner_id: "30: This profile is private"}])
        except VkApiToManyExecute:
            return self.result("fail", None, [{owner_id: "6: Too many executes"}])
        except VkApiTooManySameExecute:
            return self.result("fail", None, [{owner_id: "9: Too many same actions"}])
        except VkApiDeletedUser:
            return self.result("fail", None, [{owner_id: "18: Deleted user"}])
        except VkApiBannedUser:
            return self.result("fail", None, [{owner_id: "37: Banned user"}])
        except VkApiLimitReached:
            return self.result("fail", None, [{owner_id: "29: Limit rate"}])
        except VkApiInaccessibleContent:
            return self.result("fail", None, [{owner_id: "19: Inaccessible content"}])
        except VkApiNoAdmission:
            return self.result("fail", None, [{owner_id: "204: No admission"}])
        except VkApiReactionCanNotBeApplied:
            return self.result("fail", None, [{owner_id: "232: Reaction can not be applied to the object"}])
        except VkApiNoAdmissionToComments:
            return self.result("fail", None, [{owner_id: "212: No admission to comments"}])
        except VkApiCompileError:
            return self.result("fail", None, [{owner_id: "12: Compile error"}])
        except VkApiDoingError:
            return self.result("fail", None, [{owner_id: "13: Code execution error"}])
        except:
            return self.result("fail", None, [{owner_id: "Unknown error"}])
        if "req_err" in res_comments:
            return self.result("fail", None, [{owner_id: res_comments}])
        log.debug(f'user_id: {owner_id}; ppi: {comments_per_iteration} -> OK')
        if len(res_comments['response']) != 0:
            comments += res_comments['response']
        else:
            comments += res_comments['response']
        return self.result("success", comments, None)
