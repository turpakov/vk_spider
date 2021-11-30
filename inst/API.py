# -*- coding: utf-8 -*-
import logging
#
import itertools
import time
import re
import instagram_private_api
import instagram_web_api
#
from .exeptions import *
from settings import Settings

log = logging.getLogger(__name__)

WAIT_BETWEEN_REQUESTS = 0.3
USE_HTTP_CLIENT = False


class WEBAPIClient(instagram_web_api.Client):
    @staticmethod
    def _extract_rhx_gis(html):
        mobj = re.search(
            r'"rhx_gis":"(?P<rhx_gis>[a-f0-9]{32})"', html, re.MULTILINE)
        if mobj:
            return mobj.group('rhx_gis')
        return "4f8732eb9ba7d1c8e8897a75d6474d4eb3f5279137431b2aafb71fafe2abe178"


class Instagram:
    """
        ******************************
        Class for working with Instagram API
        ******************************
    """
    def __init__(self, settings):
        if type(settings) is not Settings:
            raise InstInvalidSettings
        self.settings = settings
        self._instaapi_sessions = set()
        self._session_generator = None
        if settings.tokens_file_vk:
            self.init_sessions(settings.tokens_file_inst)

    def init_sessions(self, auth_file_name, force=True):
        """
            Create sessions for each Instagram account
            Auth info is line of format <LOGIN>:<PASSWORD>
        """
        if force:
            log.info("Force обновил instasessions из файла {}".format(
                auth_file_name))
            self._instaapi_sessions.clear()
        log.info("Загружены данные для аккаунта инстраграма из файла {} и создана новая сессия".format(
           auth_file_name))
        for login_pass in open(auth_file_name):
            login, passwd = login_pass.strip().split(":")
            _session = WEBAPIClient(
                    auto_patch=True, authenticate=True,
                    username=login, password=passwd)\
                if USE_HTTP_CLIENT else\
                    instagram_private_api.Client(login, passwd)
            self._instaapi_sessions.add(_session)
        log.info("Полная {} сессия инстаграм.".format(
            len(self._instaapi_sessions)))
        self._session_generator = itertools.cycle(self._instaapi_sessions)

    def session(self):
        """ Create sessions for instagram API """
        if not self._session_generator:
            raise NullSessionException("Сессия для инстаграма была создана!")
        return next(self._session_generator)

    def get_userinfo(self, username):
        """ Get user info by username """
        log.debug(f"Вызван INSTAPI метод 'get_userinfo' с параметрами: {username}")
        data = self.session().user_info2(user_name=username) \
            if USE_HTTP_CLIENT else \
                self.session().username_info(user_name=username)

        if not data or not USE_HTTP_CLIENT and data.get("status", "") != "ok":
            raise NullUserDataException(f"Нет данных об инстаграм аккаунте='{username}'")
        if not USE_HTTP_CLIENT:
            data = data.get("user")
        return data

    def get_general_userinfo(self, username):
        log.debug(f"Вызван INSTAPI метод 'get_general_userinfo' с параметрами: {username}")
        target_user_info = self.get_userinfo(username)
        return {
            "user_id": target_user_info["id"] if USE_HTTP_CLIENT else target_user_info["pk"],
            "is_private": target_user_info["is_private"],
            "followers_count": target_user_info["counts"]["followed_by"] \
                if USE_HTTP_CLIENT else target_user_info["follower_count"],
            "following_count": target_user_info["counts"]["follows"] \
                if USE_HTTP_CLIENT else target_user_info["following_count"]
        }

    def _get_users_from_list(self, user_id, session_generator_function,
        session_pagination_function, session_getter_result_function,
        rank_token=None, max_count=None):
        """ Get users from account generator
            Parameters:
                session_generator_function: function for partitial generating list of accounts
                session_pagination_function: function for paginate
                session_getter_result_function: function for getting account info from request
                rank_token: objct for pagination if using secure client api
                max_count: max count of accounts
        """
        result = list()
        cur_user_index = 0
        max_id = None
        while True:
            if USE_HTTP_CLIENT:
                data_portion = session_generator_function(
                    user_id=user_id, extract=False, count=40, end_cursor=max_id)
            else:
                data_portion = session_generator_function(
                    user_id=user_id, max_id=max_id, rank_token=rank_token) if max_id else \
                    session_generator_function(user_id=user_id, rank_token=rank_token)
            if not data_portion:
                raise NullUserDataException(
                    f"Empty portion of account list data in instagram (uid='{user_id}')")

            max_id = session_pagination_function(data_portion)
            for user in session_getter_result_function(data_portion):
                result.append(user)
                cur_user_index += 1
                if cur_user_index == max_count:
                    break
            if not max_id or cur_user_index == max_count:
                break
            time.sleep(WAIT_BETWEEN_REQUESTS)
        return result

    def get_followers(self, user_id, max_count=None):
        """ Get user followers """
        log.debug(f"Вызван INSTAPI метод 'get_followers' с параметрами: {user_id}")
        _session = self.session()
        return self._get_users_from_list(user_id, _session.user_followers,
            lambda info: info.get("data", {}).get("user", {}).get("edge_followed_by", {})\
                .get("page_info", {}).get("end_cursor", {}) \
                if USE_HTTP_CLIENT else info.get("next_max_id"),
            lambda info: [u['node'] for u in info.get('data', {}).get('user', {}).get(
                    'edge_followed_by', {}).get('edges', [])] \
                    if USE_HTTP_CLIENT else info.get("users"),
            None if USE_HTTP_CLIENT else _session.generate_uuid(), max_count)

    def get_following(self, user_id, max_count=None):
        """ Get accounts by user following """
        log.debug(f"Вызван INSTAPI метод 'get_following' с параметрами: {user_id}")
        _session = self.session()
        return self._get_users_from_list(user_id, _session.user_following,
            lambda info: info.get("data", {}).get("user", {}).get("edge_follow", {})\
                .get("page_info", {}).get("end_cursor", {}) \
                if USE_HTTP_CLIENT else info.get("next_max_id"),
            lambda info: [u['node'] for u in info.get('data', {}).get('user', {}).get(
                    'edge_follow', {}).get('edges', [])] \
                    if USE_HTTP_CLIENT else info.get("users"),
            None if USE_HTTP_CLIENT else _session.generate_uuid(), max_count)

    def get_user_photos(self, user_id):
        """
        Get all user photo
        :param
            - user_id: Account id in instagram
        """
        log.debug(f"Вызван INSTAPI метод 'get_user_photos' с параметрами: {user_id}")
        result = {}
        _session = self.session()
        _first = True
        next_max_id = None
        while next_max_id or _first:
            try:
                _first = False
                results = _session.user_feed(user_id=user_id, max_id=next_max_id)
                for item in results.get('items', []):
                    try:
                        if "carousel_media" in item:
                            photo_num = item['carousel_media_count']
                            for i in range(0, photo_num):
                                id = item["carousel_media"][i]["id"]
                                photo_url = item["carousel_media"][i]["image_versions2"]["candidates"][0]["url"]
                                result[id] = photo_url
                                print(result[id])
                            continue
                        id = item["id"]
                        photo_url = item["image_versions2"]["candidates"][0]["url"]
                        result[id] = photo_url
                    except:
                        continue
                next_max_id = results.get('next_max_id')
            except:
                continue
        return result
