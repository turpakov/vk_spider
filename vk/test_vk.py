import pytest
#
from settings import settings
from vk import VK

MY_ID = 186101748
DUROV_ID = 1
DUROV_ITEM = 456264771
PUBLIC_ID = -22746750
PUBLIC_ITEM = 11427508

"""
Модуль тестирования API
USAGE: pytest --settings <setting filename> vk
"""

@pytest.fixture()
def setting(pytestconfig):
    return pytestconfig.getoption("settings")

def test_initmodule(setting):
    settings.load_JSON(setting)
    global vk_module
    vk_module = VK(settings)

def test_get_users():
    f_name = vk_module.get_users([DUROV_ID])['result'][0]['first_name']
    l_name = vk_module.get_users([DUROV_ID])['result'][0]['last_name']
    assert f_name == 'Павел'
    assert l_name == 'Дуров'

def test_get_friends():
    my_friend = vk_module.get_friends(MY_ID)['result']
    durov_friend = vk_module.get_friends(DUROV_ID)['result']
    assert len(my_friend) != 0
    assert len(durov_friend) == 0

def test_get_followers():
    followers = vk_module.get_followers(1, max_followers=100)['result']
    assert len(followers) == 100

def test_get_groups():
    groups = vk_module.get_groups(MY_ID, max_groups=10)['result']
    assert len(groups) == 10

def test_get_group_members():
    members = vk_module.get_group_members(PUBLIC_ID, max_members=100)['result']
    assert len(members) == 100

def test_get_photos():
    photos = vk_module.get_photos(DUROV_ID, max_photos=10)['result']
    assert len(photos) == 10

def test_get_wall():
    notes_durov = vk_module.get_wall(DUROV_ID, max_notes=10)['result']
    assert len(notes_durov) == 10

def test_get_videos():
    videos = vk_module.get_videos(DUROV_ID)['result']
    assert len(videos) == 4

def test_get_who_likes():
    item_id = DUROV_ITEM
    whoLikes = vk_module.get_who_likes('photo', DUROV_ID, item_id, max_likes=1000)['result']
    assert len(whoLikes) == 1000

def test_get_comments():
    item_id = DUROV_ITEM
    comments_durov = vk_module.get_comments(DUROV_ID, item_id)['result']
    barca_id = PUBLIC_ID
    item_id = PUBLIC_ITEM
    comments_barca = vk_module.get_comments(barca_id, item_id, max_comments=100)['result']
    assert comments_durov == None
    assert len(comments_barca) == 100






