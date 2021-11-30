from vk import VK

class BaseScrapper:
    """ Базовый класс для сбора"""

    def __init__(self, settings):
        self.settings = settings
        self.vk_module = VK(settings)
        #...

    def _iterator(self, *args, **kwargs):
        raise NotImplementedError

    def _filter(self, *args, **kwargs):
        raise NotImplementedError

    def _selector(self, *args, **kwargs):
        raise NotImplementedError

    def execute(self, *args, **kwargs):
        raise NotImplementedError