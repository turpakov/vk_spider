import datetime
import logging
from math import floor
from random import choice
#
from scrapping.BaseScrapper import BaseScrapper

log = logging.getLogger(__name__)


class ScrapVkUsersByRandom(BaseScrapper):
    """ Класс для сбора пользователей ВК случайным блужданием """

    def __init__(self, settings):
        self.TODAY_DATE = datetime.datetime.today()
        self.AGE_GO_TO_SCHOOL = 7
        self.AGE_WENT_FROM_SCHOOL = 17
        self.AGE_WENT_FROM_UNIVERSITY = 22
        self.MIN_NUM_OF_CLASSES = 8
        self.LEFT_SIDE_OF_AGE = 14
        self.RIGHT_SIDE_OF_AGE = 70
        super().__init__(settings)

    def _iterator(self):
        start_id = choice([i for i in range(100000, 20000000)])
        for cur_iter in range(100):
            friends = self.vk_module.get_friends(start_id)
            while(not friends["result"]):
                start_id = choice([i for i in range(100000, 20000000)])
                friends = self.vk_module.get_friends(start_id)
            friends = friends["result"]
            start_id = choice(friends)
            ans = self.vk_module.get_users(friends, ["bdate", "schools", "education"])
            if not ans.get("error"):
                for x in ans["result"]:
                    yield (x["id"], x)

    def _filter(self, data):
        for id, info in data:
            if info.get("bdate") and (info.get("schools") or info.get("education")):
                yield (id, info)

    def _selector(self, data):
        for id, info in data:
            res = {
                "id": id,
                "bday": None,
                "date_from_school": None,
                "date_from_university": None
            }
            try:
                bday = tuple(map(int, info["bdate"].split('.')[::-1]))
                if len(bday) == 3:
                    bday = datetime.datetime(*bday)
                    age = floor(((self.TODAY_DATE.year - bday.year) * 12 + (self.TODAY_DATE.month - bday.month)) / 12)
                    if self.LEFT_SIDE_OF_AGE <= age and age <= self.RIGHT_SIDE_OF_AGE:
                        log.debug(f"Возраст по дате рождения пользователя {id} равен {age}")
                        res["bday"] = info["bdate"]
                # указан год выпуска со школы
                if info["schools"]:
                    if info["schools"][0].get("year_from") and info["schools"][-1].get("year_to"):
                        age = self.TODAY_DATE.year - info["schools"][0]["year_from"] + self.AGE_GO_TO_SCHOOL
                        # исключаем случай, когда указана из нескольких школ только одна последняя
                        if self.LEFT_SIDE_OF_AGE <= age and age <= self.RIGHT_SIDE_OF_AGE and \
                                info["schools"][-1]["year_to"] - \
                                info["schools"][0]["year_from"] >= self.MIN_NUM_OF_CLASSES:
                            log.debug(f"Возраст по дате окончания школы пользователя {id} равен {age}")
                            res["date_from_school"] = info["schools"][0]["year_to"]
                    elif info["schools"][-1].get("year_graduated"):
                        age = self.TODAY_DATE.year - info["schools"][-1][
                            "year_graduated"] + self.AGE_WENT_FROM_SCHOOL
                        if self.LEFT_SIDE_OF_AGE <= age and age <= self.RIGHT_SIDE_OF_AGE:
                            log.debug(f"Возраст по дате окончания школы пользователя {id} равен {age}")
                            res["date_from_school"] = info["schools"][-1]["year_graduated"]
                # указан год выпуска из универа
                if info.get("graduation"):
                    age = self.TODAY_DATE.year - info["graduation"] + self.AGE_WENT_FROM_UNIVERSITY
                    if self.LEFT_SIDE_OF_AGE <= age and age <= self.RIGHT_SIDE_OF_AGE:
                        log.debug(f"Возраст по дате окончания универа пользователя {id} равен {age}")
                        res["date_from_university"] = info["graduation"]
                yield res
            except:
                continue

    def execute(self):
        return self._selector(self._filter(self._iterator()))
