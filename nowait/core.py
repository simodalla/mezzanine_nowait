# -*- coding: iso-8859-1 -*-

import calendar
import collections
import datetime
import inspect


def get_range_days(start_date, end_date):

    if (not isinstance(start_date, datetime.date) or
            not isinstance(end_date, datetime.date)):
        raise TypeError('both start_date and end_date must be of type'
                        ' "datetime.datetime')
    if start_date > end_date:
        raise ValueError('start_date must be greater than end_date')

    if start_date.year != end_date.year:
        raise ValueError('start_date and end_date must be dates of'
                         ' same year')

    c = calendar.Calendar()
    if start_date.month == end_date.month:
        return [date_obj for date_obj in c.itermonthdates(start_date.year,
                                                          start_date.month)
                if ((date_obj.month == start_date.month)
                    and (start_date.day <= date_obj.day <= end_date.day))]

    days = []
    for month in range(start_date.month, end_date.month + 1):
        month_days = [date_obj for date_obj in c.itermonthdates(
            start_date.year, month) if (date_obj.month == month)]
        if month == start_date.month:
            days += [date_obj for date_obj in month_days
                     if date_obj.day >= start_date.day]
        elif month == end_date.month:
            days += [date_obj for date_obj in month_days
                     if date_obj.day <= end_date.day]
        else:
            days += month_days
        del month_days
    return days


def get_week_map_by_weekday(date_list):
    args, _, _, values = inspect.getargvalues(inspect.currentframe())
    for arg in args:
        if not isinstance(values[arg], collections.Iterable):
            raise ValueError('parameter {} is not iterable'.format(arg))
    result = dict((str(weekday), list()) for weekday in range(0, 7))

    for date in date_list:
        result[str(date.weekday())].append(date)

    return result
