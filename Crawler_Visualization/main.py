#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 18-8-2 下午1:44
# @Author  : ShiMeng
# @File    : demo.py
# @Software: PyCharm
import ast
import time
import pymongo
import traceback
from ConfigParser import ConfigParser
from influxdb import InfluxDBClient
from datetime import datetime
from os.path import getmtime

"""

爬虫可视化存数据到InfluxDb 数据库脚本
采用热更新配置文件的方式
若修改配置的过程中，报错，则会使用上一次的配置信息（非首次，如果首次就报错，就会退出程序）
mongodb有验证的连接，如果你的没有用户名和密码，请按需修改
"""




# influx配置
client = InfluxDBClient(host='localhost', port=8086)
# 创建数据库
client.create_database('Spider')
client.switch_database('Spider')
#配置文件名
config_name = 'settings.conf'
WATCHED_FILES = [config_name]
WATCHED_FILES_MTIMES = [(f, getmtime(f)) for f in WATCHED_FILES]
_count_dict = {}
_size_dict = {}


def parse_config(file_name):
    try:
        cf = ConfigParser()
        cf.read(file_name)
        host = cf.get('Mongo_Uri', 'host')
        user = cf.get('Mongo_Uri', 'user')
        passwd = cf.get('Mongo_Uri', 'passwd')
        uri = 'mongodb://%s:%s@%s' % (user, passwd, host)
        interval = cf.getint('time', 'interval')
        dbs_and_cos = ast.literal_eval(cf.get('db', 'db_co_dict'))
    except:
        print "something wrong with your config file, use last setting"
        print traceback.print_exc()
        return None , None, None
    else:
        return uri, interval, dbs_and_cos


def insert_data(uri, dbs_and_cos):
    mongodb_client = pymongo.MongoClient(uri)
    for db_name, collection_name in dbs_and_cos.iteritems():
        # 数据库操作
        db = mongodb_client[db_name]
        co = db[collection_name]
        # 集合大小
        co_size = round(float(db.command("collstats", collection_name).get('size')) / 1024 / 1024, 2)
        # 集合内数据条数
        current_count = co.count()

        # 初始化，当程序刚执行时，初始量就设置为第一次执行时获取的数据
        init_count = _count_dict.get(collection_name, current_count)
        # 初始化，当程序刚执行时，初始量就设置为第一次执行时获取的数据大小
        init_size = _size_dict.get(collection_name, co_size)

        # 条数增长量
        increase_amount = current_count - init_count
        # 集合大小增长量
        increase_co_size = co_size - init_size

        current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        # 赋值
        _size_dict[collection_name] = co_size
        _count_dict[collection_name] = current_count

        json_body = [
            {
                "measurement": "crawler",
                "time": current_time,
                "tags": {
                    "spider_name": collection_name
                },
                "fields": {
                    "count": current_count,
                    "increase_count": increase_amount,
                    "size": co_size,
                    "increase_size": increase_co_size

                }
            }
        ]
        print json_body
        client.write_points(json_body)


def auto_get_new_file():
    # 热更新配置
    uri, interval, dbs_and_cos = parse_config(config_name)
    if (uri or interval or dbs_and_cos) is None:
        raise ValueError('see the error info')
    print 'Init Config:', uri, interval, dbs_and_cos
    last_uri = uri
    last_interval = interval
    last_dbs_and_cos = dbs_and_cos

    for f, mtime in WATCHED_FILES_MTIMES:
        while 1:
            if getmtime(f) != mtime:
                uri, interval, dbs_and_cos = parse_config(config_name)
                print 'Config File Changed At [%s]' % (time.strftime("%Y-%m-%d %H:%M:%S"))
                if (uri or interval or dbs_and_cos) is None:
                    print 'Used last Config'

                    uri = last_uri
                    interval = last_interval
                    dbs_and_cos = last_dbs_and_cos
                else:
                    print 'Used New Config'
                    print 'New Config:', uri, interval, dbs_and_cos
                    mtime = getmtime(f)

            insert_data(uri, dbs_and_cos)
            time.sleep(interval)

if __name__ == '__main__':
    auto_get_new_file()
