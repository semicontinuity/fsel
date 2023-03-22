import json
import os
import sys

FD_DEBUG = 101


def fd_exists(fd: int):
    try:
        os.fstat(fd)
        return True
    except OSError:
        return False


def is_primitive(obj):
    return obj is None or type(obj) is int or type(obj) is float or type(obj) is bool or type(obj) is str


def to_jsonisable(obj):
    if is_primitive(obj):
        return obj
    elif isinstance(obj, dict):
        if all((is_primitive(key) for key in obj)):
            return {
                key: to_jsonisable(value) for key, value in obj.items() if value is not None
            }
        else:
            return [
                {"key": to_jsonisable(key), "value": to_jsonisable(value)} for key, value in obj.items() if
                value is not None
            ]
    elif isinstance(obj, set):
        return to_jsonisable(list(obj))
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [to_jsonisable(e) for e in obj]
    elif isinstance(obj, bytearray):
        return [e for e in obj]
    else:
        return to_jsonisable(obj.__dict__)


DEBUG_FD_OPEN = fd_exists(FD_DEBUG)
DEBUG = os.getenv('DEBUG') or DEBUG_FD_OPEN
DEBUG_FILE = os.fdopen(FD_DEBUG, 'w') if DEBUG_FD_OPEN else sys.stderr


def debug(msg, **kwargs):
    if DEBUG == 'json':
        j = {k: to_jsonisable(v) for k, v in kwargs.items()}
        j["message"] = msg
        print(json.dumps(j), file=DEBUG_FILE)
    elif DEBUG:
        if kwargs:
            print(msg, str(kwargs), file=DEBUG_FILE)
        else:
            print(msg, file=DEBUG_FILE)
