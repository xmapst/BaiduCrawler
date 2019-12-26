#!/usr/bin/python3
# -*- coding:utf-8 -*-

import re
import sys
import ast
import ssl
import json
import zlib
import urllib
import random
import requests
import threading
import importlib
import multiprocessing
from redis import Redis
from urllib import request
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from redis.connection import BlockingConnectionPool

importlib.reload(sys)
ssl._create_default_https_context = ssl._create_unverified_context
# 增加redis的存储数据，存储类型hash
Hset_name = "crawler_data"
redis_connt = Redis(host='127.0.0.1', port=6380)
# 动态生成headers
UA = UserAgent()
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, compress',
    'Accept-Language': 'en-us;q=0.5,en;q=0.3',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': UA.chrome
}

def downLoadHtml(word):
    # 下载查询网页
    url = 'http://www.baidu.com.cn/s?wd=' + urllib.parse.quote(word) + '&pn='
    # 多线程爬取，多个页面同时爬
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    # 获取9个查询页面
    for page in range(1, 10):
        result = pool.apply_async(dataDict, (url, page))

    pool.close()
    pool.join()
 
def dataDict(url, page):
    # 获取每个页面的数据
    data_dict = {}
    # 页面链接, 百度每个页面为10-11个查询结果
    path = url + str((page - 1) * 10)
    req = request.Request(url=path, headers=headers)
    response = request.urlopen(req)
    page = response.read()

    # 解压
    gzipped = response.headers.get('Content-Encoding')
    if gzipped:
        page = zlib.decompress(page, 16+zlib.MAX_WBITS)
    
    # 利用BeautifulSoup快速提取数据
    soup = BeautifulSoup(page, 'lxml')
    div = soup.find_all('div', attrs={'class': 'result c-container'})
    promotion = soup.find_all('a', attrs={'data-is-main-url': "true", 'data-landurl': re.compile(r"^http")})
    
    # 获取百度快照数据
    for line in div:
        data = line.find('div', attrs={'class': 'c-tools'}).get('data-tools')
        data_dict = ast.literal_eval(data)
        baidu_url = requests.get(url=data_dict['url'], headers=headers, allow_redirects=False)

        real_url = baidu_url.headers['Location']
        if real_url.startswith('http'):
            data_dict['real_url'] = real_url
            data_dict['type'] = 'ordinary'
            # 插入快照数据
            redis_connt.hset(Hset_name, json.dumps(data_dict), 1)
            print(data_dict)
    
    # 获取百度推广数据
    if promotion:
        for line in promotion:
            data_dict['title'] = line.get_text()
            data_dict['url'] = line.get('href')
            data_dict['real_url'] = line.get('data-landurl')
            data_dict['type'] = 'promotion'
            # 插入推广数据
            redis_connt.hset(Hset_name, json.dumps(data_dict), 1)
            print(data_dict)

def main():
    cn = open(keyword_dict, 'r',encoding='utf8')
    # 循环关键字列表，对每个关键字进行查询匹配
    for line in cn:
        result = downLoadHtml(line.strip())
    cn.close()

if __name__ == '__main__':
    global keyword_dict = 'samples.txt'
    #### 死循环查询
    #while True:
    #    main()
    #    redis_connt.hgetall(Hset_name)
    
    #### 只查询一次
    main()
    redis_connt.hgetall(Hset_name)
    
