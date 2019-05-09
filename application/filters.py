from jinja2 import Undefined
from datetime import datetime

from application.models import FactType, EmergingFactType


def format_year(date_time):
    if date_time is not None:
        return date_time.strftime('%Y')
    return ''

def format_date(date_time):
    return date_time.strftime('%d %b %Y')


def format_month_and_year(date_time):
    return date_time.strftime('%b %Y')


def format_date_from_str(date_str):
    newdate = datetime.strptime(date_str, '%Y-%m-%d')
    return format_month_and_year(newdate)


def last_state_date(plan):
    states = plan.ordered_states()
    return states[-1]


def format_fact(name):
    if name in FactType.__members__:
        return FactType[name].value
    elif name in EmergingFactType.__members__:
        return EmergingFactType[name].value
    else:
        return name


def format_percent(value):
    return f'{value}%'


def return_percent(val1, denominator, precision=1):
    percentage = (val1 / denominator) * 100
    return round(percentage, precision)


def big_number(value):
    try:
        int(value)
    except ValueError:
        return value
    return "{:,}".format(int(value))


def format_housing_number(number):
    if number is None:
        return 'No number set for this planning authority'
    if isinstance(number, int):
        return number
    elif isinstance(number, dict):
        return number['number']
    else:
        return 'Could not find number for this planning authority'
