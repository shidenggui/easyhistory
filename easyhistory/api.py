# coding:utf-8
from .day import Day


def init(qtype, export, path):
    if qtype.lower() in ['d']:
        return Day(path=path).init(export)


def update_single_code(stock_code, path):
    return Day(path=path).update_single_code(stock_code)


def update(dtype='D', export='csv', path='history'):
    return Day(path=path).update(export)
