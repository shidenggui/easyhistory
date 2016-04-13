# coding:utf-8
import math


def get_stock_type(stock_code):
    """判断股票ID对应的证券市场
    :param stock_code:股票ID
    :return 'sh' or 'sz'"""
    if str(stock_code).startswith(('5', '6', '9')):
        return 'sh'
    return 'sz'


def get_full_code(stock_code):
    """
    :param stock_code:  股票 ID
    :return:  'sh000001' or 'sz000001'
    """
    return get_stock_type(stock_code) + stock_code


def get_quarter(month):
    return math.ceil(int(month) / 3)
