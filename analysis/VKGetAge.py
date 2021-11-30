import json
import logging
import datetime
from math import floor
import statistics
from scipy import stats as s
#
from .BaseAnalysisTask import BaseAnalysisTask
from.exeptions import *

log = logging.getLogger(__name__)

class VKGetAge(BaseAnalysisTask):
    """ Определение возраста пользователя ВК """

    def __init__(self, settings):
        self.TODAY_DATE = datetime.datetime.today()
        self.AGE_GO_TO_SCHOOL = 7
        self.AGE_WENT_FROM_SCHOOL = 17
        self.MIN_NUM_OF_CLASSES = 8
        self.LEFT_SIDE_OF_AGE = 14
        self.RIGHT_SIDE_OF_AGE = 70
        self.mean_coef = 0.35770485
        self.median_coef = 0.21777892
        self.mode_coef = -0.01540046
        self.std_coef = 0.56870139
        self.max_coef = -0.16092434
        self.min_coef = 0.06544568
        self.b_2 = 20.375543582191973
        self.a = 0.89677019
        self.b_1 = 190.14178421
        self.alpha = 0.8
        super().__init__(settings)

    def validate(self, user_id):
        try:
            info = self.vk_module.get_users([user_id])
        except:
            raise AnalysisTaskArgumentsError(f"Профиль пользователя не действителен!")
        if type(info) is not dict or info.get("deactivated"):
            raise AnalysisTaskArgumentsError(f"Профиль пользователя заблокирован!")
        if (type(info) is not dict or
                info.get("is_closed") and not info.get("can_access_closed")):
            raise AnalysisTaskArgumentsError(f"Профиль пользователя скрыт!")

    def _create_search_params_from_userinfo(self, info, age_from=14, age_to=70):
        """ Get json with search params from user info """
        uid = info.get("id")
        domain = info.get("domain")
        if domain and uid and not domain.endswith(str(uid)):
            name = domain
        else:
            name = info.get("name")
            if not name:
                name = info.get("first_name") + " " + info.get("last_name")
        search_params = {
            "q": name,
            "has_photo": 1 if info.get("photo_id") or \
                              info.get("photo_max") and info.get(
                "photo_max") != "https://vk.com/images/camera_100.png?ava=1" else 0,
            "count": 1000,
        }
        if info.get("bdate"):
            bdate = info.get("bdate").split(".")
            if len(bdate) < 3:
                search_params.update({"birth_day": bdate[0],
                                      "birth_month": bdate[1], })
            if len(bdate) == 3:
                search_params["birth_year"] = bdate[2]
        if info.get("city"):
            search_params["city"] = info.get("city").get("id")
        if info.get("country"):
            search_params["country"] = info.get("country").get("id")
        if info.get("home_town"):
            search_params["hometown"] = info.get("home_town")
        if info.get("sex"):
            search_params["sex"] = info.get("sex")
        search_params["age_from"] = age_from
        search_params["age_to"] = age_to
        return search_params

    def _get_age_by_info(self, info):
        """ Get age by info of user """
        uid = info.get("id")
        if not uid:
            return None
        search_json = self._create_search_params_from_userinfo(info, "$age_from", "$age_to")
        search_json = json.dumps(search_json, ensure_ascii=False) \
            .replace('"$age_from"', "age_from") \
            .replace('"$age_to"', "age_to")
        code = """
        var uid = """ + str(uid) + """;""" + """
        int age_from = 14;
        int age_to = 80;
        var search_json = """ + search_json + """;
        var tmp_search_json = search_json;
        if( API.users.search(tmp_search_json).items@.id.indexOf(uid) == -1 )
        {
            return 0;
        }
        while( age_from != age_to )
        {
            tmp_search_json = search_json;
            int pivot = age_from + age_to;
            if( pivot % 2 == 0 )
            {
                pivot = pivot / 2;
            }
            else
            {
                pivot = (pivot - 1) / 2;
            }
            tmp_search_json.age_from = age_from;
            tmp_search_json.age_to = pivot;
            if( API.users.search(tmp_search_json).items@.id.indexOf(uid) != -1 )
            {
                if( age_to - age_from == 1 )
                {
                    age_to = age_from;
                }
                else
                {
                    age_to = pivot;
                }
            }
            else
            {
                if( age_to - age_from == 1 )
                {
                    age_from = age_to;
                }
                else
                {
                    age_from = pivot;
                }
            }
        }
        return age_from;
        """
        age = self.vk_module._vkapi_request("execute", {"code": code})["response"]
        log.debug(f"Определен возраст пользователя ВК (uid={uid}). Приблизительный возраст={age}")
        if age is None:
            return None
        elif age == 0:
            return None
        return int(age)

    def _simple_det_age_of_vk_user(self, user_ids: list):
        """"
            Simple method to determine age of users
            return: age or error or None
        """
        result = []
        all_info = self.vk_module.get_users(user_ids, ["bdate"])["result"]
        #указана дата в профиле
        for info in all_info:
            if "bdate" in info:
                bday = tuple(map(int, info["bdate"].split('.')[::-1]))
                if len(bday) == 3:
                    bday = datetime.datetime(*bday)
                    age = floor(((self.TODAY_DATE.year - bday.year) * 12 + (self.TODAY_DATE.month - bday.month)) / 12)
                    if self.LEFT_SIDE_OF_AGE <= age and age <= self.RIGHT_SIDE_OF_AGE:
                        result.append({info["id"]: age})
        return result

    def _det_year_graduated(self, user_ids: list):
        """"
            Method to determine year of users graduated
            return: year or error or None
        """
        result = []
        all_info = self.vk_module.get_users(user_ids, ["schools"])["result"]
        # указан год выпуска со школы
        for info in all_info:
            if info.get("schools"):
                num_of_schools = len(info["schools"])
                if num_of_schools:
                    if info["schools"][-1].get("year_graduated"):
                        year = info["schools"][-1]["year_graduated"]
                        log.debug(f"Определен год окончания школы пользователя ВК (uid={info['id']}). Год={year}")
                        result.append(year)
                    if info["schools"][0].get("year_from") and info["schools"][-1].get("year_to"):
                        year = info["schools"][-1]["year_to"]
                        # исключаем случай, когда указана из нескольких школ только одна последняя
                        if info["schools"][-1]["year_to"] - \
                            info["schools"][0]["year_from"] >= self.MIN_NUM_OF_CLASSES:
                            log.debug(f"Определен год окончания школы пользователя ВК (uid={info['id']}). Год={year}")
                            result.append(year)
        return result

    def det_age_of_vk_user(self, user_id: int, num_of_iter: int=2):
        """"
            Determine age of user
            return: age
        """
        #если указан явно возраст
        age_simple = self._simple_det_age_of_vk_user([user_id])
        if age_simple:
            return list(age_simple[0].values())[0]

        #пытаемся определить по поиску
        info = self.vk_module.get_users([user_id], ["bdate", "education", "schools", "home_town"])["result"][0]
        age_simple = self._get_age_by_info(info)
        if age_simple is not None:
            return age_simple

        #не удалось определить простым способом
        year_grad = self._det_year_graduated([user_id])
        if year_grad:
        #указан год окончания школы
            year_by_school = round(year_grad[0] * self.a + self.b_1)
            age = self.TODAY_DATE.year - year_by_school
            log.debug(f"Определен примерный возраст пользователя ВК (uid={user_id}). Возраст={age}")
            return age

        #ничего не указано, итеративный способ
        age = None
        friends_of_target = self.vk_module.get_friends(user_id)["result"]
        log.debug(f"Функция get_friends вернула: {friends_of_target}")
        if friends_of_target:
            friends_of_target_ages_dict = self._simple_det_age_of_vk_user(friends_of_target)
            friends_of_target_ages = [list(i.values())[0] for i in friends_of_target_ages_dict]
            if len(friends_of_target_ages) >= 3:
                friends_of_target_ages.remove(max(friends_of_target_ages))
                friends_of_target_ages.remove(min(friends_of_target_ages))
                friends_with_age = [list(i.keys())[0] for i in friends_of_target_ages_dict]
                friends_without_age = [i for i in friends_of_target if i not in friends_with_age]
                if friends_of_target_ages:
                    mean = statistics.mean(friends_of_target_ages)
                    median = statistics.median(friends_of_target_ages)
                    std = statistics.pstdev(friends_of_target_ages)
                    mode = int(s.mode(friends_of_target_ages)[0])
                    max_ = max(friends_of_target_ages)
                    min_ = min(friends_of_target_ages)
                    fr_age = self.mean_coef * mean + self.median_coef * median + self.mode_coef * mode + self.std_coef * std + self.max_coef * max_ + self.min_coef * min_ + self.b_2
                    age = fr_age
                    log.debug(f"Определен примерный возраст пользователя ВК (uid={user_id}). Возраст={age}")
                    if num_of_iter == 1:
                        return age

                if num_of_iter >= 2:
                    new_friends_ages_dict = self._simple_det_age_of_vk_user(friends_without_age)
                    new_friends_ages = [list(i.values())[0] for i in new_friends_ages_dict]
                    friends_of_target_ages += new_friends_ages
                    if friends_of_target_ages and new_friends_ages:
                        mean = statistics.mean(friends_of_target_ages)
                        median = statistics.median(friends_of_target_ages)
                        std = statistics.pstdev(friends_of_target_ages)
                        mode = int(s.mode(friends_of_target_ages)[0])
                        max_ = max(friends_of_target_ages)
                        min_ = min(friends_of_target_ages)
                        fr_age = self.mean_coef * mean + self.median_coef * median + self.mode_coef * mode + self.std_coef * std + self.max_coef * max_ + self.min_coef * min_ + self.b_2
                        if age:
                            age = age * self.alpha + fr_age * (1 - self.alpha)
                        else:
                            age = fr_age
                        log.debug(f"Определен примерный возраст пользователя ВК (uid={user_id}). Возраст={age}")

            return age

    def execute(self, user_id):
        self.validate(user_id)
        return self.det_age_of_vk_user(user_id)
