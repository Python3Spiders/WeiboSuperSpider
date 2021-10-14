# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# create_time:      2021/9/11 21:20
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# 微信公众号         月小水长

import requests

from lxml import etree

from time import sleep

import csv

import traceback

import sys

import os

class WeiboComPostSpider():
    headers = {
        'authority': 'weibo.com',
        'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
        'x-xsrf-token': 'O0-ImAktE3C1RzDjl6WiFqFl',
        'traceparent': '00-c86118ff53dcfc555ae1df4137154561-37c770d7f7d605f9-00',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
        'accept': 'application/json, text/plain, */*',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://weibo.com/u/1516153080?tabtype=article',
        'accept-language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
        'cookie': '看不见我'
    }

    params = {
        'uid': '1516153080',
        'page': '1',
        'feature': '10',
    }

    post_folder = 'post'

    timeout = 10

    sleep_sec_per_request = 3

    save_per_page = 3

    def initData(self):
        self.params['uid'] = str(self.uid)
        self.params['page'] = str(self.start_page)

        self.got_post = []
        self.got_post_num = 0
        self.written_post_num = 0

        self.post_author = None
        self.result_file = None



    def __init__(self, uid, start_page = 1, cookie=None):
        self.uid = uid

        self.start_page = start_page

        if cookie:
            self.headers['cookie'] = cookie

        if not os.path.exists(self.post_folder):
            os.mkdir(self.post_folder)

        self.initData()

    def writeCsv(self):
        """将爬取的信息写入csv文件"""
        try:
            result_headers = [
                'mid',
                'title',
                'url',
                'created_at',
                'reads_count',
                'reposts_count',
                'comments_count',
                'attitudes_count',
                'detail'
            ]

            result_data = [w.values() for w in self.got_post][self.written_post_num:]

            with open(self.result_file, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                if self.written_post_num == 0:
                    writer.writerows([result_headers])
                writer.writerows(result_data)
            print('%d条微博文章写入csv文件完毕:' % self.got_post_num)
            self.written_post_num = self.got_post_num
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def finish(self, reason):
        self.writeCsv()
        print(reason)
        sys.exit()

    def parseDetail(self, detail_url):
        response = requests.get(url=detail_url, headers=self.headers, timeout=self.timeout)

        html = etree.HTML(response.text)

        ps = html.xpath('//p')

        all_text = []

        for p in ps:

            img = p.xpath('.//img/@src')
            if img:
                all_text.append(img[0])

            text = p.xpath('.//text()')
            if text and len(text[0]) > 0:
                all_text.append(text[0])

        all_text = '\n'.join(all_text)

        print(all_text)

        return all_text


    def run(self):

        while True:
            response = requests.get('https://weibo.com/ajax/statuses/mymblog',
                                    headers=self.headers, params=self.params, timeout=self.timeout)
            post_list = response.json()['data']['list']
            if len(post_list) == 0:
                self.finish('post list is none')
                break


            for post in post_list:

                if not self.post_author:
                    self.post_author = post['user']['screen_name']
                    self.result_file = os.path.join(self.post_folder, f'{self.post_author}.csv')

                detail_url = post['url_struct'][0]['long_url']

                mid = post['mid']

                title = post['url_struct'][0]['url_title']

                url = detail_url

                created_at = post['created_at']

                reads_count = post['reads_count']

                reposts_count = post['reposts_count']

                comments_count = post['comments_count']

                attitudes_count = post['attitudes_count']

                print(detail_url)

                post_detail = self.parseDetail(detail_url)

                self.got_post.append({
                    'mid': mid,
                    'title': title,
                    'url': url,
                    'created_at': created_at,
                    'reads_count': reads_count,
                    'reposts_count': reposts_count,
                    'comments_count': comments_count,
                    'attitudes_count': attitudes_count,
                    'detail': post_detail
                })

                self.got_post_num += 1

                sleep(self.sleep_sec_per_request)

            self.start_page += 1
            self.params['page'] = self.start_page

            # if (self.start_page+1) % self.save_per_page == 0:
            #     self.writeCsv()


if __name__ == '__main__':
    # 指定想要爬取的微博用户的 id，可以设置 start_page 起始翻页参数，一般用不到
    # 修改 cookie 可以直接参数指定，也可以在 self.headers 中直接修改
    WeiboComPostSpider(2803301701).run()

'''
KeyError: 'data'
说明需要换 cookie
https://weibo.com/u/1516153080?tabtype=article 打开该网页，找到 mymblog 请求
'''