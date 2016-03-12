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

