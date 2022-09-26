import logging
import datetime as dt
from dateutil.parser import parse

logger = logging.getLogger(__name__)


def dt_from_json(dct):
    for k, v in dct.items():
        if isinstance(v, str) and "DATE: " in v:
            try:
                dct[k] = parse(v.replace("DATE:", ""))
            except Exception as e:
                logger.error(f"Issue parsing date {v}. Error: {str(e)}")
    return dct


def dt_to_json(value):
    if isinstance(value, dt.datetime):
        return f"DATE: {value.isoformat()}"
    return value
