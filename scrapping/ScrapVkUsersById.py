import datetime
import logging
from math import floor
#
from scrapping.BaseScrapper import BaseScrapper

log = logging.getLogger(__name__)


class ScrapVkUsersById(BaseScrapper):
    """ Класс для сбора пользователей ВК с заданным диапазоном id"""

    def __init__(self, settings):
        self.TODAY_DATE = datetime.datetime.today()
        self.AGE_GO_TO_SCHOOL = 7
        self.AGE_WENT_FROM_SCHOOL = 17
        self.AGE_WENT_FROM_UNIVERSITY = 22
        self.MIN_NUM_OF_CLASSES = 8
        self.LEFT_SIDE_OF_AGE = 14
        self.RIGHT_SIDE_OF_AGE = 70
        super().__init__(settings)

    def _iterator(self, left_side, right_side):
        for id in range(left_side, right_side + 1, 500):
            users = [id + i for i in range(500)]
            ans = self.vk_module.get_users(users, ["bdate"])
            if not ans.get("error"):
                for x in ans["result"]:
                    yield (x["id"], x)

    def _filter(self, data):
        for id, info in data:
            if info.get("bdate"):
                yield (id, info)

    def _selector(self, data):
        for id, info in data:
            res = {
                "id": id,
                "bday": None
            }
            try:
                bday = tuple(map(int, info["bdate"].split('.')[::-1]))
                if len(bday) == 3:
                    bday = datetime.datetime(*bday)
                    age = floor(((self.TODAY_DATE.year - bday.year) * 12 + (self.TODAY_DATE.month - bday.month)) / 12)
                    if self.LEFT_SIDE_OF_AGE <= age and age <= self.RIGHT_SIDE_OF_AGE:
                        log.debug(f"Возраст по дате рождения пользователя {id} равен {age}")
                        res["bday"] = info["bdate"]
                        yield res
            except:
                continue

    def execute(self, left_side, right_side):
        return self._selector(self._filter(self._iterator(left_side, right_side)))
