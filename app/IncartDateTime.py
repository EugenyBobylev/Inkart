"""
 Date amd time processing module
"""
import configparser
import datetime
import os

from config import Config


def get_today() -> datetime.date:
    today = datetime.date.today()
    return today


def get_tomorrow() -> datetime.date:
    today: datetime.date = get_today()
    tomorrow: datetime.date = today + datetime.timedelta(days=1)
    return tomorrow


def get_night_start() -> datetime.time:
    ini_night_start = get_str_from_ini("night_start")
    night_start = datetime.time.fromisoformat(ini_night_start)
    return night_start


def get_night_finish() -> datetime.time:
    ini_night_finish = get_str_from_ini("night_finish")
    night_finish = datetime.time.fromisoformat(ini_night_finish)
    return night_finish


def get_today_night_start() -> datetime.datetime:
    today: datetime.date = get_today()
    night_start: datetime.time = get_night_start()
    today_night_start = datetime.datetime.combine(today, night_start)
    return today_night_start


def get_tomorrow_night_finish() -> datetime.datetime:
    tomorrow: datetime.date = get_tomorrow()
    night_finish: datetime.time = get_night_finish()
    tomorrow_night_finish: datetime.datetime = datetime.datetime.combine(tomorrow, night_finish)
    return tomorrow_night_finish


def get_str_from_ini(param: str) -> str:
    ini = os.path.join(Config.BASEPATH, 'incart.ini')
    config = configparser.ConfigParser()
    config.read(ini)
    value = config["DEFAULT"][param]
    return value


def add_minutes(dt: datetime.datetime, minutes: int) -> datetime.datetime:
    """
     изменим (добавим или вычтем) значение метки времени на указанной кол. минут
    :param dt: метка времени
    :param minutes: значение в минутах на которе изменим метку времени
    :return: измененное значение метки времени
    """
    datetime_value = dt + datetime.timedelta(minutes=minutes)
    return datetime_value


def round_datetime(dt: datetime.datetime, precision: int = 10) -> datetime.datetime:
    """
    округлить метку времени до точности заданной минутами от 1  до 60
    :param dt: метка времени до округления
    :param precision: точность округления времени в минутах
    :return:  метка времени после округления
    """
    hours = precision // 60  # will need to add hours
    minutes = precision % 60  # will need to add minutes
    rounded_minute = 0
    rounded_datetime = dt.replace(minute=rounded_minute, second=0, microsecond=0)
    if dt.minute != 0:
        rounded_minute = dt.minute - (dt.minute % minutes)
        delta = datetime.timedelta(hours=hours, minutes=minutes)
        rounded_datetime = dt.replace(minute=rounded_minute, second=0, microsecond=0)
        rounded_datetime = rounded_datetime + delta
    return rounded_datetime


def get_local_timezone() -> datetime.timezone:
    now_utc = datetime.datetime.utcnow()
    now = datetime.datetime.now()
    delta = now - now_utc
    local_tz = datetime.timezone(offset=delta)
    return local_tz


def to_utc_datetime(datetimestr: str) -> datetime.datetime:
    dt = datetime.datetime.strptime(datetimestr, '%Y-%m-%dT%H:%M:%S %Z')
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    return dt


def to_local_datetime(dt: datetime) -> datetime:
    local_zone = get_local_timezone()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo= datetime.timezone.utc)
    local_dt = dt.astimezone(local_zone)
    return local_dt
