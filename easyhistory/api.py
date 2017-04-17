# coding:utf-8
from rqalpha.data.base_data_source import BaseDataSource
import pandas as pd
import easyutils
import datetime
import os

from .day import Day


def init(dtype='D', export='csv', path='history'):
    return Day(path=path, export=export).init()


def update_single_code(dtype='D', stock_code=None, path='history', export='csv'):
    if stock_code is None:
        raise Exception('stock code is None')
    return Day(path=path, export=export).update_single_code(stock_code)


def update(dtype='D', export='csv', path='history'):
    return Day(path=path, export=export).update()


def history(stock_code, market=None, bundle_path='~/.rqalpha/bundle'):
    d = BaseDataSource(os.path.expanduser(bundle_path))

    instruments = d._instruments.get_all_instruments()

    stock_map = {i.order_book_id: i for i in instruments}
    if not market:
        market = easyutils.get_stock_type(stock_code)
    if market == 'sh':
        stock_code += '.XSHG'
    else:
        stock_code += '.XSHE'
    raw = d._all_day_bars_of(stock_map[stock_code])
    df = pd.DataFrame.from_dict(raw)
    df.set_index('datetime', inplace=True)
    return df

#
