# coding: utf-8
import csv
from datetime import timedelta
import json
import math
import os
import random
import re
import time
from datetime import datetime
from functools import partial
from multiprocessing.pool import Pool, ThreadPool

import requests
from pyquery import PyQuery

from . import helpers


class Day:
    SINA_API = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_FuQuanMarketHistory/stockid/{stock_code}.phtml'
    SINA_API_HOSTNAME = 'vip.stock.finance.sina.com.cn'
    STOCK_CODE_API = 'http://218.244.146.57/static/all.csv'

    def __init__(self, dtype='D', path='history'):
        self.path = os.path.join(path, 'day')
        self.result_path = os.path.join(self.path, 'data')
        self.raw_path = os.path.join(self.path, 'raw_data')

        self.factor_cols = {'close', 'open', 'high', 'low', 'amount'}
        self.history_order = ['date', 'open', 'high', 'close', 'low', 'volume', 'amount', 'factor']

    def init(self, export='csv'):
        if not os.path.exists(self.result_path):
            os.makedirs(self.result_path)
        if not os.path.exists(self.raw_path):
            os.makedirs(self.raw_path)

        stock_codes = self.get_all_stock_codes()
        if os.path.exists(os.path.join(self.raw_path)):
            exists_codes = [code[:-4] for code in os.listdir(self.raw_path) if code.endswith('.csv')]
        else:
            exists_codes = set()
        stock_codes = set(stock_codes).difference(exists_codes)

        pool = ThreadPool(1)
        func = partial(self.out_stock_history, export=export)
        pool.map(func, stock_codes)

    def update(self, export='csv'):
        """ 更新已经下载的历史数据
        :param export: 历史数据的导出方式，目前支持持 csv
        :return:
        """
        stock_codes = []
        for file in os.listdir(self.raw_path):
            if not file.endswith('.json'):
                continue
            stock_code = file[:6]
            stock_codes.append(stock_code)

        pool = Pool(10)
        func = partial(self.update_single_code)
        if export.lower() in ['csv']:
            pool.map(func, stock_codes)

    def update_single_code(self, stock_code):
        """ 更新对应的股票文件历史行情
        :param stock_code: 股票代码
        :return:
        """
        updated_data = self.get_update_day_history(stock_code)
        self.update_file(updated_data, stock_code)
        self.gen_history_result(stock_code)

    def get_update_day_history(self, stock_code):
        summary_path = os.path.join(self.raw_path, '{}_summary.json'.format(stock_code))
        with open(summary_path) as f:
            summary = json.load(f)
        data_year = int(summary['year'])
        data_quarter = helpers.get_quarter(summary['month'])
        now_year = datetime.now().year

        # 使用下一天的日期作为更新起始日，避免季度末时多更新上一季度的内容
        tomorrow = datetime.now() + timedelta(days=1)
        now_quarter = helpers.get_quarter(tomorrow.month)

        updated_data = list()
        for year in range(data_year, now_year + 1):
            for quarter in range(1, 5):
                if year == now_year:
                    if quarter > now_quarter:
                        continue
                elif year == data_year:
                    if quarter < data_quarter:
                        continue
                updated_data += self.get_quarter_history(stock_code, year, quarter)
        updated_data.sort(key=lambda day: day[0])
        return updated_data

    def update_file(self, updated_data, stock_code):
        csv_file_path = os.path.join(self.raw_path, '{}.csv'.format(stock_code))
        self.update_csv_file(csv_file_path, updated_data)
        self.write_summary_file(stock_code, updated_data)

    def update_csv_file(self, file_path, updated_data):
        with open(file_path) as f:
            f_csv = csv.reader(f)
            old_history = [l for l in f_csv][1:]
        update_start_day = updated_data[0][0]
        old_clean_history = [day for day in old_history if day[0] < update_start_day]
        new_history = old_clean_history + updated_data
        new_history.sort(key=lambda day: day[0])
        self.write_csv_file(file_path, new_history)

    def get_all_stock_codes(self):
        rep = requests.get(self.STOCK_CODE_API)
        stock_codes = re.findall(r'\r\n(\d+)', rep.content.decode('gbk'))
        random.shuffle(stock_codes)
        return stock_codes

    def out_stock_history(self, stock_code, export='csv'):
        all_history = self.get_all_history(stock_code)
        if len(all_history) <= 0:
            return
        if export == 'csv':
            file_path = os.path.join(self.raw_path, '{}.csv'.format(stock_code))
            print(file_path)
            self.write_csv_file(file_path, all_history)
            self.write_summary_file(stock_code, all_history)
            self.gen_history_result(stock_code)

        return all_history

    def write_csv_file(self, file_path, history):
        with open(file_path, 'w') as f:
            f.write('date,open,high,close,low,volume,amount,factor\n')
            for day_line in history:
                write_line = '{},{},{},{},{},{},{},{}\n'.format(*day_line)
                f.write(write_line)

    def write_summary_file(self, stock_code, history):
        file_path = os.path.join(self.raw_path, '{}_summary.json'.format(stock_code))
        with open(file_path, 'w') as f:
            latest_day = datetime.strptime(history[-1][0], '%Y-%m-%d')
            summary = dict(
                    year=latest_day.year,
                    month=latest_day.month,
                    day=latest_day.day,
                    date=latest_day.strftime('%Y-%m-%d')
            )
            json.dump(summary, f)

    def gen_history_result(self, stock_code):
        csv_path = os.path.join(self.raw_path, '{}.csv'.format(stock_code))
        with open(csv_path) as f:
            f_csv = csv.DictReader(f)
            day_history = [day for day in f_csv]
        factor = float(max(day_history, key=lambda x: float(x['factor']))['factor'])
        new_history = []
        for day_data in day_history:
            for col in day_data:
                if col in self.factor_cols:
                    day_data[col] = round(float(day_data[col]) / factor, 2)
            ordered_item = []
            for col in self.history_order:
                ordered_item.append(day_data[col])
            new_history.append(ordered_item)
            stock_path = os.path.join(self.result_path, '{}.csv'.format(stock_code))
        self.write_csv_file(stock_path, new_history)

    def get_all_history(self, stock_code):
        years = self.get_stock_time(stock_code)
        all_history = []
        for year in years:
            year_history = self.get_year_history(stock_code, year)
            all_history += year_history
        all_history.sort(key=lambda day: day[0])
        return all_history

    def get_year_history(self, stock_code, year):
        year_history = []
        now_year = datetime.now().year
        now_month = datetime.now().month
        end_quarter = 5 if str(year) != str(now_year) else math.ceil(now_month / 12) + 1
        for quarter in range(1, end_quarter):
            quarter_data = self.get_quarter_history(stock_code, year, quarter)
            if quarter_data is None:
                continue
            year_history += quarter_data
        return year_history

    def get_stock_time(self, stock_code):
        # 获取年月日
        url = self.SINA_API.format(stock_code=stock_code)
        try:
            dom = PyQuery(url)
        except requests.ConnectionError:
            return []
        year_options = dom('select[name=year] option')
        years = [o.text for o in year_options][::-1]
        return years

    def get_quarter_history(self, stock_code, year, quarter):
        year = int(year)
        if year < 1990:
            return list()
        params = dict(
                year=year,
                jidu=quarter
        )
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'
        }
        print('request {},{},{}'.format(stock_code, year, quarter))
        url = self.SINA_API.format(stock_code=stock_code)
        rep = list()
        loop_nums = 10
        for i in range(loop_nums):
            try:
                rep = requests.get(url, params, timeout=3, headers=headers)
                break
            except requests.ConnectionError:
                time.sleep(60)
            except Exception as e:
                with open('error.log', 'a+') as f:
                    f.write(str(e))

        print('end request {}, {}, {}'.format(stock_code, year, quarter))
        if rep is None:
            with open('error.txt', 'a+') as f:
                f.write('{},{},{}'.format(stock_code, year, quarter))
            return list()
        res = self.handle_quarter_history(rep.text)
        return res

    def handle_quarter_history(self, rep_html):
        dom = PyQuery(rep_html)
        raw_trows = dom('#FundHoldSharesTable tr')
        empty_history_nodes = 2
        if len(raw_trows) <= empty_history_nodes:
            return list()

        unused_head_index_end = 2
        trows = raw_trows[unused_head_index_end:]

        res = list()
        for row_td_list in trows:
            td_list = row_td_list.getchildren()
            day_history = []
            for i, td in enumerate(td_list):
                td_content = td.text_content()
                date_index = 0
                if i == date_index:
                    td_content = re.sub(r'\r|\n|\t', '', td_content)
                day_history.append(td_content)
            self.convert_stock_data_type(day_history)
            res.append(day_history)
        return res

    def convert_stock_data_type(self, day_data):
        """将获取的对应日期股票数据除了日期之外，转换为正确的 float / int 类型
        :param day_data: ['2016-02-19', '945.019', '949.701', '940.336', '935.653', '31889824.000', '320939648.000', '93.659']
        :return: ['2016-02-19', 945.019, 949.701, 940.336, 935.653, 31889824.000, 320939648.000, 93.659]
        """
        date_index = 0

        for i, val in enumerate(day_data):
            if i == date_index:
                continue
            day_data[i] = float(val)
