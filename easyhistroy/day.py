import csv
import json
import math
import os
import random
import re
import socket
import time
from datetime import datetime
from multiprocessing.pool import Pool, ThreadPool

import requests
from pyquery import PyQuery

from . import helpers


class Day:
    SINA_API = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_FuQuanMarketHistory/stockid/{stock_code}.phtml'
    SINA_API_HOSTNAME = 'vip.stock.finance.sina.com.cn'
    STOCK_CODE_API = 'http://218.244.146.57/static/all.csv'

    def init(self, export='csv', path='out'):
        # 获取数据
        # 校验完整性
        # 记录出错的数据 / 或者
        # ip = socket.gethostbyname(self.SINA_API_HOSTNAME)
        # self.SINA_API = self.SINA_API % ip
        print(self.SINA_API)
        stock_codes = self.get_all_stock_codes()
        pool = ThreadPool(1)
        params = [(code, export, path) for code in stock_codes]
        pool.starmap(self.out_stock_history, params)

    def update(self, export='csv', path='out'):
        stock_codes = []
        for file in os.listdir(os.path.join(path, 'raw_data')):
            if not file.endswith('csv'):
                continue
            stock_code = file[:-4]
            stock_codes.append(stock_code)
        pool = Pool(10)
        params = [(code, path) for code in stock_codes]
        if export.lower() in ['csv']:
            pool.starmap(self.update_single_code, params)

    def update_single_code(self, stock_code, path):
        updated_data = self.get_update_day_history(stock_code, path)
        self.update_file(updated_data, stock_code, path)

    def get_update_day_history(self, stock_code, path='out'):
        summary_path = os.path.join(path, 'raw_data', '{}_summary.json'.format(stock_code))
        with open(summary_path) as f:
            summary = json.load(f)
        data_year = summary['year']
        data_quarter = helpers.get_quarter(summary['month'])
        now_year = datetime.now().year
        now_quarter = helpers.get_quarter(datetime.now().month)
        updated_data = []
        for year in range(data_year, now_year + 1):
            for quarter in range(1, 5):
                if year == data_year:
                    if quarter < data_quarter:
                        continue
                elif year == now_year:
                    if quarter > now_quarter:
                        continue
                updated_data += self.get_quarter_history(stock_code, year, quarter)
        updated_data.sort(lambda day: day[0])
        return updated_data

    def update_file(self, updated_data, stock_code, path='out'):
        csv_file_path = os.path.join(path, 'raw_data', '{}.csv'.format(stock_code))
        self.update_csv_file(csv_file_path, updated_data)
        self.write_summary_file(stock_code, path, updated_data)

    def update_csv_file(self, file_path, updated_data):
        with open(file_path) as f:
            f_csv = csv.reader(f)
        latest_day = updated_data[-1][0]
        old_history = [l for l in f_csv][1:]
        old_clean_history = [day for day in old_history if day < latest_day]
        new_history = old_clean_history + updated_data
        new_history.sort(key=lambda day: day[0])
        self.write_csv_file(file_path, new_history)

    def get_all_stock_codes(self):
        rep = requests.get(self.STOCK_CODE_API)
        stock_codes = re.findall(r'\r\n(\d+)', rep.content.decode('gbk'))
        random.shuffle(stock_codes)
        return stock_codes

    def out_stock_history(self, stock_code, export='csv', path='out'):
        all_history = self.get_all_history(stock_code)
        if export == 'csv':
            parent_dir = os.path.join(path, 'raw_data')
            if not os.path.exists(path):
                os.makedirs(parent_dir)
            file_path = os.path.join(parent_dir, '{}.csv'.format(stock_code))
            print(file_path)
            self.write_csv_file(file_path, all_history)
            # summary_file = os.path.join(parent_dir, '{}_summary.json'.format(stock_code))
            self.write_summary_file(stock_code, path, all_history)

        return all_history

    def write_csv_file(self, file_path, history):
        with open(file_path, 'w') as f:
            f.write('date,open,high,close,low,volume,amount,factor\n')
            for day_line in history:
                write_line = '{},{},{},{},{},{},{},{}\n'.format(*day_line)
                f.write(write_line)

    def write_summary_file(self, stock_code, path, history):
        file_path = os.path.join(path, 'raw_data', '{}_summary.json'.format(stock_code))
        with open(file_path, 'w') as f:
            latest_day = history[-1][0]
            year = latest_day[:4]
            quarter = latest_day[5: 7]
            day = latest_day[8: 9]
            summary = dict(
                    year=year,
                    quarter=quarter,
                    day=day,
                    date=latest_day
            )
            json.dump(summary, f)

    def get_all_history(self, stock_code):
        years = self.get_stock_time(stock_code)
        all_histroy = []
        for year in years:
            year_history = self.get_year_history(stock_code, year)
            all_histroy += year_history
        all_histroy.sort(key=lambda day: day[0])
        return all_histroy

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
        dom = PyQuery(url)
        year_options = dom('select[name=year] option')
        years = [o.text for o in year_options][::-1]
        return years

    def get_quarter_history(self, stock_code, year, quarter):
        params = dict(
                year=year,
                jidu=quarter
        )
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'
        }
        print('request {},{},{}'.format(stock_code, year, quarter))
        url = self.SINA_API.format(stock_code=stock_code)
        rep = None
        loop_nums = 10
        for i in range(loop_nums):
            try:
                rep = requests.get(url, params, timeout=40, headers=headers)
            except requests.ConnectionError:
                time.sleep(60)
            except Exception as e:
                with open('error.log', 'a+') as f:
                    f.write(str(e))

        print('end request %s' % stock_code)
        if rep is None:
            with open('error.txt', 'a+') as f:
                f.write('{},{},{}'.format(stock_code, year, quarter))
            return []
        res = self.handle_quarter_history(rep.text)
        return res

    def handle_quarter_history(self, rep_html):
        dom = PyQuery(rep_html)
        raw_trows = dom('#FundHoldSharesTable tr')
        empty_history_nodes = 2
        if len(raw_trows) <= empty_history_nodes:
            return None

        unused_head_index_end = 2
        trows = raw_trows[unused_head_index_end:]

        res = []
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
