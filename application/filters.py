from jinja2 import Undefined
from datetime import datetime

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


def sort_plans(plans):
	if plans is None or isinstance(plans, Undefined) or len(plans) == 1:
		return plans

	return sorted(plans, key=last_state_date, reverse=True)
