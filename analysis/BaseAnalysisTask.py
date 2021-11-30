from vk import VK

class BaseAnalysisTask:
    """ Базовый класс для аналитических задач """

    def __init__(self, settings):
        self.settings = settings
        self.vk_module = VK(settings)
        # ...

    def info(self):
        return BaseAnalysisTask.__doc__

    def validate(self, *args, **kwargs):
        """ Осуществляет проверку входных параметров на корректность """
        raise NotImplementedError()

    def execute(self, *args, **kwargs):
        """ Выполняет аналитическую задачу """
        raise NotImplementedError()