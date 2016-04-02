# coding:utf-8
import os

import pandas as pd
import talib


class Indicator(object):
    def __init__(self, stock_code, history):
        self.stock_code = stock_code
        self.history = history

    def load_csv_files(self, path):
        file_list = [f for f in os.listdir(path) if f.endswith('.csv')]
        for stock_csv in file_list:
            csv_ext_index_start = -4
            stock_code = stock_csv[:csv_ext_index_start]
            self.market[stock_code] = pd.read_csv(stock_csv, index_col='date')

    def __getattr__(self, item):
        def talib_func(*args, **kwargs):
            str_args = ''.join(map(str, args))
            if self.history.get(item + str_args) is not None:
                return self.history
            func = getattr(talib, item)
            res_arr = func(self.history['close'].values, *args, **kwargs)
            self.history[item + str_args] = res_arr
            return self.history

        return talib_func


class History(object):
    def __init__(self, dtype='D', path='history'):
        self.market = dict()
        data_path = os.path.join(path, 'day', 'data')
        self.load_csv_files(data_path)

    def load_csv_files(self, path):
        file_list = [f for f in os.listdir(path) if f.endswith('.csv')]
        for stock_csv in file_list:
            csv_ext_index_start = -4
            stock_code = stock_csv[:csv_ext_index_start]

            csv_path = os.path.join(path, stock_csv)
            self.market[stock_code] = Indicator(stock_code, pd.read_csv(csv_path, index_col='date'))

    def __getitem__(self, item):
        return self.market[item]
