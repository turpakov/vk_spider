import os
import re
#
from .BaseScrapper import BaseScrapper
from .utils import walk_modules, get_classes


class Scrapper:
    """ Класс для сбора """

    def __init__(self, settings):
        classes = get_classes(walk_modules(os.path.dirname(os.path.abspath(__file__)).split("\\")[-1]))
        for name, obj in classes:
            if name != BaseScrapper.__name__:
                task = obj(settings)
                setattr(self, self._translate_method(name), task.execute)

    def _translate_method(self, class_method_name):
        replacer = lambda m: f"{('_' if m.start(0) > 0 else '')}{m.group()}"
        return re.sub("[A-Z]{2,}", replacer,
                      re.sub("[A-Z][^A-Z_]+", replacer, class_method_name)).lower()
