from time import localtime, strftime
from typing import Callable
from datetime import datetime, timedelta, time, date

import yaml
from tornado.ioloop import IOLoop

from client import OTClient


def schedule(interval: int):
    """Scheduler

    Runs a given function as decorator with given interval

    Parameters
    ----------
    interval: integer
        Time in hours
    """
    dt = timedelta(hours=interval)
    def func_wrapper(func):
        def wrapper(*args, **kwargs):
            t = localtime()
            current_time = strftime("%H:%M:%S", t)
            def inner():
                func(*args, **kwargs)
                wrapper(*args, **kwargs)
            IOLoop.current().add_timeout(dt, inner)
        return wrapper
    return func_wrapper


@schedule(interval=2)
def fetch_houses(config: str, redirect: Callable):
    with open(config) as f:
        params = yaml.load(f)

    with OTClient() as c:
        for entry in c.query(**params):
            redirect(entry)
