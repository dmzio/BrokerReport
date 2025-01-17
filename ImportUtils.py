import binascii
import csv
from collections import OrderedDict
from datetime import date, datetime, timedelta

import xlrd


def fixNumber(string):
    if type(string) is float:
        return str(string)
    ret = ""
    s = string
    if len(s.split(",")) == 2 and "." not in s:
        s = s.replace(",", ".")
    for x in s:
        if x in "0123456789.-":
            ret += x
    return ret


def cleanText(string):
    return string.encode("ascii", errors="ignore").decode("ascii", errors="ignore")


def getCsv(filename, delimiter=";", encoding="ascii"):
    try:
        with open(filename, newline="", encoding=encoding, errors="ignore") as f:
            reader = csv.reader(f, delimiter=delimiter)
            values = [row for row in reader]
            ids = list(range(0, len(values[0])))
            return [OrderedDict(list(zip(values[0], row)) + list(zip(ids, row))) for row in values[1:]]
    except:
        return None


def getExcel(filename):
    try:
        return xlrd.open_workbook(filename)
    except:
        return None


def checksum(text):
    return "%08X" % (binascii.crc32(text.encode("ascii", errors="ignore")) & 0xFFFFFFFF)
