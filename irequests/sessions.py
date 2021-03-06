import random
import time
import hashlib
#
import requests
import logging
#

log = logging.getLogger(__name__)


def _get_user_agent():
    """
    Create new user agent
    Arguments:

    Return:
        result: user_agent: str
    """
    platform = random.choice(['Macintosh', 'Windows', 'X11'])
    if platform == 'Macintosh':
        os = random.choice(['68K', 'PPC'])
    elif platform == 'Windows':
        os = random.choice(['Win3.11',
                            'WinNT3.51',
                            'WinNT4.0',
                            'Windows NT 5.0',
                            'Windows NT 5.1',
                            'Windows NT 5.2',
                            'Windows NT 6.0',
                            'Windows NT 6.1',
                            'Windows NT 6.2',
                            'Win95',
                            'Win98',
                            'Win 9x 4.90',
                            'WindowsCE'])
    elif platform == 'X11':
        os = random.choice(['Linux i686', 'Linux x86_64'])
    browser = random.choice(['chrome', 'firefox', 'ie'])
    if browser == 'chrome':
        webkit = str(random.randint(500, 599))
        version = str(random.randint(0, 24)) + '.0' + \
            str(random.randint(0, 1500)) + '.' + str(random.randint(0, 999))
        return 'Mozilla/5.0 (' + os + ') AppleWebKit/' + webkit + \
               '.0 (KHTML, live Gecko) Chrome/' + version + ' Safari/' + webkit
    elif browser == 'firefox':
        year = str(random.randint(2000, 2012))
        month = random.randint(1, 12)
        if month < 10:
            month = '0' + str(month)
        else:
            month = str(month)
        day = random.randint(1, 30)
        if day < 10:
            day = '0' + str(day)
        else:
            day = str(day)
        gecko = year + month + day
        version = random.choice(['1.0',
                                 '2.0',
                                 '3.0',
                                 '4.0',
                                 '5.0',
                                 '6.0',
                                 '7.0',
                                 '8.0',
                                 '9.0',
                                 '10.0',
                                 '11.0',
                                 '12.0',
                                 '13.0',
                                 '14.0',
                                 '15.0'])
        return 'Mozilla/5.0 (' + os + '; rv:' + version + \
               ') Gecko/' + gecko + ' Firefox/' + version
    elif browser == 'ie':
        version = str(random.randint(1, 10)) + '.0'
        engine = str(random.randint(1, 5)) + '.0'
        option = random.choice([True, False])
        if option:
            token = random.choice(['.NET CLR', 'SV1', 'Tablet PC', 'Win64; IA64', 'Win64; x64', 'WOW64']) + '; '
        elif not option:
            token = ''
        return 'Mozilla/5.0 (compatible; MSIE ' + version + \
               '; ' + os + '; ' + token + 'Trident/' + engine + ')'


def create_session():
    """
    Create new session
    Arguments:

    Return:
        result: requests.session()
    """
    session = requests.session()
    session.headers = {
        'User-Agent': _get_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml,application/pdf;q=0.9,image/'
                  'webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate'
    }
    google_id = hashlib.md5(
        str(random.randint(0, 16**16)).encode()).hexdigest()[: 16]
    cookie = {
        "domain": ".scholar.google.com",
        "expires": time.time() + 60 * 60,
        "name": "GSP",
        "value": 'ID={}:CF=3'.format(google_id),
        "httpOnly": False
    }
    session.cookies.set(cookie['name'], cookie['value'])
    session.HTTP_requests = 0
    return session
