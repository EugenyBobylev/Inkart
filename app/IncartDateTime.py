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


def get_str_from_ini(param:str) -> str:
    ini = os.path.join(Config.BASEPATH, 'incart.ini')
    config = configparser.ConfigParser()
    config.read(ini)
    value = config["DEFAULT"][param]
    return value
