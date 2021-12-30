# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# create_time:      2021/10/13 8:30
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# 微信公众号         月小水长
import hashlib

import requests

import os

from lxml import etree

import pandas as pd

import traceback

from urllib.parse import parse_qs

from time import sleep


class WeiboSuperTopicActiveUserSpider():
    headers = {
        'authority': 'weibo.com',
        'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        'content-type': 'application/x-www-form-urlencoded',
        'x-requested-with': 'XMLHttpRequest',
        'sec-ch-ua-mobile': '?0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36',
        'sec-ch-ua-platform': '"Windows"',
        'accept': '*/*',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://weibo.com/p/1008088fd92f4f79feef9d97ff90d2ff2f3127/topic_album?from=page_100808&mod=TAB',
        'accept-language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
        'cookie': '占位而已，在外部传入 cookie 即可'
    }

    params = {
        'api': 'http://i.huati.weibo.com/pcpage/papp',
        'ajwvr': '6',
        'atype': 'all',
        'viewer_uid': '1739046981',
        'since_id': '',
        'page_id': '1008088fd92f4f79feef9d97ff90d2ff2f3127',
        'page': '2',
        'ajax_call': '1',
        'appname': 'album',
        'module': 'feed',
        'is_feed': '1',
        '__rnd': '1634086158596',
    }

    image_root_folder = 'image'

    slp_per_req = 3

    def initTitle(self):
        response = requests.get(f'https://weibo.com/p/{self.super_topic_id}/super_index', headers=self.headers)
        html = etree.HTML(response.text)
        title = html.xpath('//title/text()')[0]
        self.title = title[:title.index('—')] + '活跃粉丝'

    def __init__(self, super_topic_id, cookie=None):
        self.super_topic_id = super_topic_id
        if cookie:
            self.headers['cookie'] = cookie

        if not os.path.exists(self.image_root_folder):
            os.mkdir(self.image_root_folder)

        self.image_group_folder = os.path.join(self.image_root_folder, self.super_topic_id)
        if not os.path.exists(self.image_group_folder):
            os.mkdir(self.image_group_folder)

        self.active_uid = []
        self.page = 2
        self.since_id = None

        self.params['page_id'] = self.super_topic_id

        self.initTitle()

    def downloadImg(self, image_url):
        image_spilt = image_url.rsplit('.', 1)
        image_path = os.path.join(self.image_group_folder,
                                  '{}.{}'.format(hashlib.md5(image_spilt[0].encode('utf-8')).hexdigest(),
                                                 image_spilt[1]))
        if os.path.exists(image_path):
            return
        print(f'** downloading {image_url} **')
        with open(image_path, 'wb') as fp:
            response = requests.get(image_url, headers=self.headers)
            fp.write(response.content)

    def parseHtml(self, response):
        html = etree.HTML(response.json()['data'])
        photos = html.xpath('//a[@class="ph_ar_box"]')
        if photos == None or len(photos) == 0:
            return False
        for index, photo in enumerate(photos):
            action_data = photo.xpath('./@action-data')[0]
            params = parse_qs(action_data)

            uid, since_id = params['uid'][0], params['since_id'][0]

            if index == 0:
                self.since_id = since_id

            mid, pid = params['mid'][0], params['pid'][0]

            pic_url = f'https://wx2.sinaimg.cn/mw690/{pid}.jpg'

            print(pic_url)

            self.downloadImg(pic_url)

            if uid in self.active_uid:
                continue
            else:
                self.active_uid.append(uid)
        return True

    def run(self):
        while True:
            self.params['page'] = str(self.page)
            if self.since_id:
                self.params['since_id'] = str(self.since_id)
            try:
                response = requests.get('https://weibo.com/p/aj/proxy',
                                        headers=self.headers,
                                        params=self.params)
                flag = self.parseHtml(response)
            except:
                print(traceback.format_exc())
                break
            if not flag or self.page > 1000000:
                break

            self.page += 1
            sleep(self.slp_per_req)

            print(f'------------- page {self.page} -------------')

        print(self.active_uid)
        df = pd.DataFrame({
            'user_link': [f'https://weibo.com/u/{uid}' for uid in self.active_uid]
        })
        df.to_csv(f'{self.title}.csv', index=False, encoding='utf-8-sig')


def main(super_topic_id, cookie):
    WeiboSuperTopicActiveUserSpider(super_topic_id, cookie).run()


if __name__ == '__main__':
    # 必须是登录了新版 weibo.com，然后打开超话主页的相册 tab 例如
    # https://weibo.com/p/10080868ed174b2d302045692b38756ee47f21/topic_album?from=page_100808&mod=TAB#place
    # 下拉，复制 /p/aj/proxy 接口的 cookie
    WeiboSuperTopicActiveUserSpider(
        super_topic_id='在此处替换 super_topic_id 例如： 10080868ed174b2d302045692b38756ee47f21',
        cookie='在此处替换 cookie'

    ).run()
