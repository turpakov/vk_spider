class BaseInstError(Exception):
    """ Ошибка при работе с Instagram """


class NullSessionException(BaseInstError):
    """ Ошибка при создании сессии """


class NullUserDataException(BaseInstError):
    """ Ошибка при получении данных """


class InstInvalidToken(BaseInstError):
    """ Токен пользователя не действителен """


class InstInvalidSettings(BaseInstError):
    """ Заданные параметры не корректны """
