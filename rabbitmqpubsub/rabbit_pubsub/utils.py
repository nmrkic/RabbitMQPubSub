import logging
import datetime as dt
from dateutil.parser import parse
import base64

logger = logging.getLogger(__name__)


def dict_from_json(dct):
    for k, v in dct.items():
        if isinstance(v, str):
            if "DATE: " in v:
                try:
                    dct[k] = parse(v.replace("DATE:", ""))
                except Exception as e:
                    logger.error(f"Issue parsing date {v}. Error: {str(e)}")
            elif "BYTES: " in v:
                try:
                    dct[k] = base64.b64decode(v.replace("BYTES:", ""))
                except Exception as e:
                    logger.error(f"Issue decoding bytes {v}. Error: {str(e)}")
    return dct


def dict_to_json(value):
    if isinstance(value, dt.datetime):
        return f"DATE: {value.isoformat()}"
    elif isinstance(value, bytes):
        return f"BYTES: {base64.b64encode(value).decode('utf-8')}"
    return value
