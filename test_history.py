import unittest
import easyhistory.day
import easyhistory

from datetime import datetime
class TestHistory(unittest.TestCase):
    def test_get_history(self):
        test_date = '000001'
        normal_data = [str(y) for y in range(1991, datetime.now().year + 1)]
        res = easyhistory.day.Day().get_stock_time(test_date)

        self.assertListEqual(res, normal_data)

    def test_get_quarter_history(self):
        test_data = ['000001', 2016, 1]
        normal_data = ['2016-02-19', 945.019, 949.701, 940.336, 935.653, 31889824.000, 320939648.000, 93.659]
        res = easyhistory.day.Day().get_quarter_history(*test_data)
        print(res)

    def test_day_data_type_convert(self):
        test_data = ['2016-02-19', '945.019', '949.701', '940.336', '935.653', '31889824.000', '320939648.000', '93.659']
        normal_data = ['2016-02-19', 945.019, 949.701, 940.336, 935.653, 31889824.000, 320939648.000, 93.659]
        easyhistory.day.Day().convert_stock_data_type(test_data)
        self.assertListEqual(test_data, normal_data)

    def test_out_history(self):
        test_data = ['002783']
        easyhistory.day.Day().out_stock_history(*test_data)

    def test_day_init(self):
        easyhistory.init('D', export='csv', path='out')

if __name__ == '__main__':
    unittest.main()

