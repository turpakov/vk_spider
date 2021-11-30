import traceback
#
import requests
import logging
#
from .sessions import create_session


log = logging.getLogger(__name__)


def request(URL: str, data: dict, format_JSON=False, method="POST"):
    """
    Make request
    Arguments:
        URL:str - URL request
        data:dict - parameters for executed request
        format_JSON:bool - return result as json
    Return:
        result: json or text content
    """
    log.debug(f"Execute request '{URL}' with params {data}")
    try:
        sess = create_session()
        response = (sess.post if method == "POST" else sess.get)(url=URL, data=data)
        result = response.json() if format_JSON else response.content
    except requests.exceptions.Timeout:
        return {"req_err": "TIMEOUT"}
    except requests.exceptions.ConnectionError:
        return {"req_err": "ConnectionError"}
    except requests.exceptions.HTTPError:
        return {"req_err": "HTTPError"}
    except:
        return {
            "req_err": "Unknown error", 
            "traceback": traceback.format_exc()
            }
    return result
