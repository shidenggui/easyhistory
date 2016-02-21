from .day import Day


def init(qtype, export, path):
    if qtype.lower() in ['d']:
        return Day().init(export, path)
