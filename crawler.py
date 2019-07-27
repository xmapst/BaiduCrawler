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

Hset_name = "crawler_data"
redis_connt = Redis(host='127.0.0.1', port=6380)
UA = UserAgent()
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, compress',
    'Accept-Language': 'en-us;q=0.5,en;q=0.3',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': UA.chrome
}

def get_proxy():
    return requests.get("http://118.24.52.95:5010/get/").content

def downLoadHtml(word):
    url = 'http://www.baidu.com.cn/s?wd=' + urllib.parse.quote(word) + '&pn='
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    for page in range(1, 10):
        result = pool.apply_async(dataDict, (url, page))

    pool.close()
    pool.join()
 
def dataDict(url, page):
    data_dict = {}
    path = url + str((page - 1) * 10)
    req = request.Request(url=path, headers=headers)
    response = request.urlopen(req)
    page = response.read()

    gzipped = response.headers.get('Content-Encoding')
    if gzipped:
        page = zlib.decompress(page, 16+zlib.MAX_WBITS)
    else:
        page = page

    soup = BeautifulSoup(page, 'lxml')
    div = soup.find_all('div', attrs={'class': 'result c-container'})
    promotion = soup.find_all('a', attrs={'data-is-main-url': "true", 'data-landurl': re.compile(r"^http")})

    for line in div:
        data = line.find('div', attrs={'class': 'c-tools'}).get('data-tools')
        data_dict = ast.literal_eval(data)
        baidu_url = requests.get(url=data_dict['url'], headers=headers, allow_redirects=False)

        real_url = baidu_url.headers['Location']
        if real_url.startswith('http'):
            data_dict['real_url'] = real_url
            data_dict['type'] = 'ordinary'
            #redis_connt.hset(Hset_name, json.dumps(data_dict), 1)
            print(data_dict)

    if promotion:
        for line in promotion:
            data_dict['title'] = line.get_text()
            data_dict['url'] = line.get('href')
            data_dict['real_url'] = line.get('data-landurl')
            data_dict['type'] = 'promotion'
            #redis_connt.hset(Hset_name, json.dumps(data_dict), 1)
            print(data_dict)

def main():
    cn = open(keyword_dict, 'r',encoding='utf8')
    for line in cn:
        result = downLoadHtml(line.strip())
    cn.close()

if __name__ == '__main__':
    global keyword_dict
    keyword_dict = 'samples.txt'
    while True:
        main()
        redis_connt.hgetall(Hset_name)
