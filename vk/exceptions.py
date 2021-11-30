class BaseVkError(Exception):
    """ Ошибка при работе с ВКонтакте """


class VkApiProfileIsPrivate(BaseVkError):
    """ Профиль пользователя ВК имеет частный доступ """


class VkApiToManyExecute(BaseVkError):
    """ Много запросов """


class VkApiTooManySameExecute(BaseVkError):
    """ Много одинаковых действий """


class VkApiDeletedUser(BaseVkError):
    """ Профиль пользователя ВК удален """


class VkApiLimitReached(BaseVkError):
    """ Превышен лимит запросов """


class VkApiBannedUser(BaseVkError):
    """ Профиль пользователя ВК заблокирован """


class VkApiLimitedListOfGroups(BaseVkError):
    """ Доступ к запрошенному списку групп ограничен настройками приватности пользователя """


class VkApiInaccessibleContent(BaseVkError):
    """ Контент недоступен """


class VkInvalidToken(BaseVkError):
    """ Токен пользователя не действителен """


class VkInvalidSettings(BaseVkError):
    """ Заданные параметры не корректны """


class VkApiNoAdmission(BaseVkError):
    """ Нет доступа """


class VkApiReactionCanNotBeApplied(BaseVkError):
    """ Действие неприменимо к объекту """


class VkApiBadIdOfGroup(BaseVkError):
    """ Недопустимый идентификатор сообщества """


class VkApiNoAdmissionToComments(BaseVkError):
    """ Нет доступа к комментариям """


class VkApiCompileError(BaseVkError):
    """ Невозможно скомпилировать код """


class VkApiDoingError(BaseVkError):
    """ Ошибка выполнения кода """



