import pytest
#
from settings import settings
from inst import Instagram

MY_ID = 1458924954
MY_USERNAME = "daniel_turpakov"


"""
Модуль тестирования API
USAGE: pytest --settings <setting filename> inst
"""

@pytest.fixture()
def setting(pytestconfig):
    return pytestconfig.getoption("settings")

def test_initmodule(setting):
    settings.load_JSON(setting)
    global inst_module
    inst_module = Instagram(settings)

def test_get_userinfo():
    id = inst_module.get_userinfo(MY_USERNAME)['pk']
    assert id == MY_ID

def test_get_general_userinfo():
    id = inst_module.get_general_userinfo(MY_USERNAME)["user_id"]
    assert id == MY_ID

def test_get_followers():
    followers = inst_module.get_followers(MY_ID)
    assert len(followers) >= 200

def test_get_following():
    followings = inst_module.get_following(MY_ID)
    assert len(followings) >= 100

def test_get_user_photos():
    photos = inst_module.get_user_photos(MY_ID)
    assert len(photos) >= 10