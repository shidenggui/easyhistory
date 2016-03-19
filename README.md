# easyhistory
用于获取维护股票的历史数据

### 引入

```python
import easyhistory
```

### 初始化日线历史数据

```python
easyhistory.init('D', export='csv', path='history')
```

注1： 下载后的原始数据在 `path/day/raw_data` 下, 复权后数据在  `path/day/data` 下

注2: 下载所有股票的历史数据需要很长时间，后面应该会直接提供百度盘或者其他方式，然后再更新

### 更新

```python
easyhistory.update('D', export='csv', path='history')
```

### 指标系统

目前还在测试中，指标计算使用了 `talib` 和 `pandas`

* tablib 安装: https://github.com/mrjbq7/ta-lib
* pandas: pip install pandas

#### 使用

```python
his = easytrader.History(dtype='D', path='行情目录')

# MA 计算, 直接调用的 talib 的对应函数
res = his['000001'].MA(5)


# 返回的是 pandas 的 dataframe 格式

             open   high  close    low     volume      amount  factor     MA5
date                                                                         
2016-03-10  10.24  10.35  10.15  10.13  506112.94  5193459.68  93.659  10.268
2016-03-11  10.10  10.22  10.16  10.04  409716.87  4160186.89  93.659  10.220

```

注: [talib 可用指标](https://github.com/mrjbq7/ta-lib) 以及 [pandas 相关](https://github.com/pydata/pandas)
