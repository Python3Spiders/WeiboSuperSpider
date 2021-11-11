# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# create_time:      2021/11/6 23:23
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# 微信公众号         月小水长

import requests

import os

import csv

import traceback

from time import sleep

from datetime import datetime, timedelta

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def parseTime(publish_time):
    if '刚刚' in publish_time:
        publish_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    elif '分钟' in publish_time:
        minute = publish_time[:publish_time.find('分钟')]
        minute = timedelta(minutes=int(minute))
        publish_time = (datetime.now() -
                        minute).strftime('%Y-%m-%d %H:%M')
    elif '小时' in publish_time:
        hour = publish_time[:publish_time.find('小时')]
        hour = timedelta(hours=int(hour))
        publish_time = (datetime.now() -
                        hour).strftime('%Y-%m-%d %H:%M')
    elif '今天' in publish_time:
        today = datetime.now().strftime('%Y-%m-%d')
        time = publish_time[3:]
        publish_time = today + ' ' + time
    elif '月' in publish_time:
        # 补 0 对齐
        if publish_time.index('月') == 1:
            publish_time = '0' + publish_time
        if publish_time.index('日') == 4:
            publish_time = publish_time[:3] + '0' + publish_time[3:]
        year = datetime.now().strftime('%Y')
        month = publish_time[0:2]
        day = publish_time[3:5]
        time = publish_time[7:12]
        publish_time = year + '-' + month + '-' + day + ' ' + time
    else:
        publish_time = publish_time[:16]
    return publish_time


import json


class WeiboLikeSpider(object):
    cookie = '你的 cookie'

    headers = {
        'authority': 'm.weibo.cn',
        'sec-ch-ua': '"Google Chrome";v="95", "Chromium";v="95", ";Not A Brand";v="99"',
        'x-xsrf-token': '60c414',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36',
        'accept': 'application/json, text/plain, */*',
        'mweibo-pwa': '1',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://m.weibo.cn/detail/4467107636950632',
        'accept-language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
    }

    params = {
        'id': '4467107636950632',
        'page': '1',
    }

    # 每个 request 休眠 8 s
    slp_sec_per_req = 8

    # 每个 request 连接超时 8 s
    timeout = 8

    # 每翻 5 页保存一次
    save_per_n_page = 5

    # 结果 csv 文件所在的文件夹
    like_folder = 'like'

    def initConfig(self):
        self.headers['cookie'] = self.cookie
        self.params['id'] = str(self.wid)
        self.params['page'] = str(self.page)

        self.ss = requests.Session()

    def __init__(self, wid, page=1, cookie=None, proxies=None):
        self.wid = wid
        self.page = page
        if cookie:
            self.cookie = cookie
        self.proxies = proxies
        self.initConfig()

        self.got_likes = []
        self.got_likes_num = 0
        self.written_likes_num = 0

        if not os.path.exists(self.like_folder):
            os.mkdir(self.like_folder)
        self.result_file = os.path.join(self.like_folder, f'{self.wid}.csv')

    def get_response(self):
        while True:
            res = self.ss.get(url='https://m.weibo.cn/api/attitudes/show',
                              params=self.params, timeout=self.timeout,
                              headers=self.headers, verify=False, proxies=self.proxies)
            try:
                res_json = res.json()
            except:
                print('\n\n')
                print(res.text)
                print('res json decoder from None')
                break

            if 'data' in res_json.keys() and not res_json['data']['data'] == None:
                print(res_json)
                return res
            with open('error_msg.json', 'w', encoding='utf-8-sig') as f:
                f.write(json.dumps(res_json, indent=2, ensure_ascii=False))
            print(f'res json data is none {res.url}')
        print('\n\n\n ----------- 准备退出，请重新运行 -----------')
        return None

    def write_csv(self):
        """将爬取的信息写入csv文件"""
        try:
            result_headers = [
                'lid',
                'publish_time',
                'user_name',
                'user_link',
                'source',
                'user_verified_type'
            ]

            result_data = [w.values() for w in self.got_likes][self.written_likes_num:]

            with open(self.result_file, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                if self.written_likes_num == 0:
                    writer.writerows([result_headers])
                writer.writerows(result_data)
            print('%d条 like 写入csv文件完毕:' % self.got_likes_num)
            self.written_likes_num = self.got_likes_num
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def run(self):
        while True:
            self.params['page'] = self.page
            print(f'---- parse page : {self.page}  ----')
            try:
                response = self.get_response()
                data = response.json()['data']['data']
                print(f'---- parse url : {response.url}  ----')
                if data == None or len(data) == 0:
                    print('data is none')
                    break
                for item in data:
                    lid = item['id']
                    publish_time = parseTime(item['created_at'])
                    user_name = item['user']['screen_name']
                    user_link = "https://weibo.com/u/" + str(item['user']['id'])
                    source = item['source']
                    user_verified_type = item['user']['verified_type']

                    print(publish_time, user_name, source)

                    self.got_likes.append({
                        'lid': lid,
                        'publish_time': publish_time,
                        'user_name': user_name,
                        'user_link': user_link,
                        'source': source,
                        'user_verified_type': user_verified_type
                    })
                    self.got_likes_num += 1
            except:
                print(traceback.format_exc())
                break

            if self.page % self.save_per_n_page == 0 and self.got_likes_num > self.written_likes_num:
                self.write_csv()

            self.page += 1

            sleep(self.slp_sec_per_req)
        if self.got_likes_num > self.written_likes_num:
            self.write_csv()


if __name__ == '__main__':
    # proxies = {
    #     'http': 'http://115.29.170.58:8118',
    #     'https': 'http://115.29.170.58:8118',
    # }
    WeiboLikeSpider(wid='4467107636950632').run()
