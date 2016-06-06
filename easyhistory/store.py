# coding: utf8
import json
import os
from datetime import datetime

import easyutils
import pandas as pd


def use(export='csv', **kwargs):
    if export.lower() in ['csv']:
        return CSVStore(**kwargs)


class Store:
    def load(self, stock_data):
        pass

    def write(self, stock_code, data):
        pass


class CSVStore(Store):
    def __init__(self, path, dtype):
        if dtype.lower() in ['d']:
            self.path = os.path.join(path, 'day')
        self.result_path = os.path.join(self.path, 'data')
        self.raw_path = os.path.join(self.path, 'raw_data')

    def write(self, stock_code, updated_data):
        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)
        if not os.path.exists(self.raw_path):
            os.makedirs(self.raw_path)

        csv_file_path = os.path.join(self.raw_path, '{}.csv'.format(stock_code))
        if os.path.exists(csv_file_path):
            try:
                his = pd.read_csv(csv_file_path)
            except ValueError:
                return

            updated_data_start_date = updated_data[0][0]
            old_his = his[his.date < updated_data_start_date]
            updated_his = pd.DataFrame(updated_data, columns=his.columns)
            his = old_his.append(updated_his)
        else:
            his = pd.DataFrame(updated_data,
                               columns=['date', 'open', 'high', 'close', 'low', 'volume', 'amount', 'factor'])
        his.to_csv(csv_file_path, index=False)
        date = his.iloc[-1].date
        self.write_summary(stock_code, date)
        self.write_factor_his(stock_code, his)

    def get_his_stock_date(self, stock_code):
        summary_path = os.path.join(self.raw_path, '{}_summary.json'.format(stock_code))
        with open(summary_path) as f:
            summary = json.load(f)
        latest_date = datetime.strptime(summary['date'], '%Y-%m-%d')
        return latest_date

    def write_summary(self, stock_code, date):
        file_path = os.path.join(self.raw_path, '{}_summary.json'.format(stock_code))
        with open(file_path, 'w') as f:
            latest_day = datetime.strptime(date, '%Y-%m-%d')
            summary = dict(
                    year=latest_day.year,
                    month=latest_day.month,
                    day=latest_day.day,
                    date=date
            )
            json.dump(summary, f)

    def write_factor_his(self, stock_code, his):
        result_file_path = os.path.join(self.result_path, '{}.csv'.format(stock_code))
        factor_cols = his.columns.difference(['date'])
        his[factor_cols] = his[factor_cols] / his.factor.max()
        his.to_csv(result_file_path, index=False)

    @property
    def init_stock_codes(self):
        stock_codes = easyutils.stock.get_all_stock_codes()
        exists_codes = set()
        if os.path.exists(self.raw_path):
            code_slice = slice(-4)
            exists_codes = {code[code_slice] for code in os.listdir(self.raw_path) if code.endswith('.csv')}
        return set(stock_codes).difference(exists_codes)

    @property
    def update_stock_codes(self):
        code_slice = slice(6)
        return [f[code_slice] for f in os.listdir(self.raw_path) if f.endswith('.json')]
