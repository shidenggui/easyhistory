from .day import Day


def init(qtype, export, path):
    if qtype.lower() in ['d']:
        return Day().init(export, path)

def update_single_code(stock_code, path):
    return Day().update_single_code(stock_code, path)
