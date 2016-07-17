# coding: utf-8
import math
import re
import time
from datetime import datetime
from datetime import timedelta
from multiprocessing.pool import ThreadPool

import requests
from pyquery import PyQuery

from . import helpers
from . import store


class Day:
    SINA_API = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vMS_FuQuanMarketHistory/stockid/{stock_code}.phtml'
    SINA_API_HOSTNAME = 'vip.stock.finance.sina.com.cn'
    STOCK_CODE_API = 'http://218.244.146.57/static/all.csv'

    def __init__(self, path='history', export='csv'):
        self.store = store.use(export=export, path=path, dtype='D')

    def init(self):
        stock_codes = self.store.init_stock_codes
        pool = ThreadPool(10)
        pool.map(self.init_stock_history, stock_codes)

    def update(self):
        """ 更新已经下载的历史数据 """
        stock_codes = self.store.update_stock_codes
        pool = ThreadPool(2)
        pool.map(self.update_single_code, stock_codes)

    def update_single_code(self, stock_code):
        """ 更新对应的股票文件历史行情
        :param stock_code: 股票代码
        :return:
        """
        latest_date = self.store.get_his_stock_date(stock_code)
        updated_data = self.get_update_day_history(stock_code, latest_date)
        
        if len(updated_data) == 0 or len(updated_data[0]) == 0:
            return 

        self.store.write(stock_code, updated_data)

    def get_update_day_history(self, stock_code, latest_date):
        data_year = latest_date.year
        data_quarter = helpers.get_quarter(latest_date.month)
        now_year = datetime.now().year
        # 使用下一天的日期作为更新起始日，避免季度末时多更新上一季度的内容
        tomorrow = datetime.now() + timedelta(days=1)
        now_quarter = helpers.get_quarter(tomorrow.month)

        updated_data = list()
        for year in range(data_year, now_year + 1):
            for quarter in range(1, 5):
                if year == data_year:
                    if quarter < data_quarter:
                        continue
                if year == now_year:
                    if quarter > now_quarter:
                        continue
                # if year == now_year:
                #     if quarter > now_quarter:
                #         continue
                # elif year == data_year:
                #     if quarter < data_quarter:
                #         continue
                updated_data += self.get_quarter_history(stock_code, year, quarter)
        updated_data.sort(key=lambda day: day[0])
        return updated_data

    def init_stock_history(self, stock_code):
        all_history = self.get_all_history(stock_code)
        if len(all_history) <= 0:
            return
        self.store.write(stock_code, all_history)

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
        end_quarter = 5 if str(year) != str(now_year) else math.ceil(now_month / 3) + 1
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
