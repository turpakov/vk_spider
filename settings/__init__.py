import traceback
#
import logging
import json
#
from .exceptions import *


class Settings:
    def __init__(self):
        self.log_format = "%(asctime)s|%(levelname)s|%(name)s|%(funcName)s|#%(lineno)d|%(message)s"
        self.log_level = logging.DEBUG
        self.log_file = "log/default.log"
        self.log_max_bytes_in_file = 1024 * 1024 * 10 # 10 Mib
        #
        self.tokens_file_vk = None
        self.tokens_file_tg = None
        self.tokens_file_inst = None
        #
        self.encoding = "utf-8"

    def load_JSON(self, fname):
        """ Загрузка настроек из файла в формате JSON """
        try:
            for key, value in json.loads(
                    open(fname, "r", encoding=self.encoding).read()).items():
                setattr(self, key, value)
        except:
            print(traceback.format_exc())
            raise SettingsLoadError()

    def save_JSON(self, fname):
        """ Сохранение настроек в файл в формате JSON """
        try:
            open(fname, "w", encoding=self.encoding).write(
                json.dumps(vars(self)))
        except:
            print(traceback.format_exc())
            raise SettingsSaveError()


settings = Settings()