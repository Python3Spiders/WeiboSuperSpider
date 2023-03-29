# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# create_time:      2023/2/13 17:53
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# website           https://buyixiao.github.io/
# 微信公众号         月小水长

import requests

headers = {
    'authority': 'weibo.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
    'client-version': 'v2.38.9',
    'referer': 'https://weibo.com/u/1788052133',
    'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'server-version': 'v2023.02.13.1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}
from time import sleep

slp_sec_per_req = 8

import traceback
from datetime import datetime


def time_formater(input_time_str):
    input_format = '%a %b %d %H:%M:%S %z %Y'
    output_format = '%Y-%m-%d %H:%M:%S'
    return datetime.strptime(input_time_str, input_format).strftime(output_format)


def getLongText(mid):
    params = {
        'ajwvr': '6',
        'mid': str(mid),
        'is_settop': '',
        'is_sethot': '',
        'is_setfanstop': '',
        'is_setyoudao': '',
        'is_from_ad': '0',
        '__rnd': '1640166514672',
    }
    try:
        response = requests.get('https://weibo.com/p/aj/mblog/getlongtext', headers=headers, params=params)
        print(response.url)
        return response.json()['data']['html']
    except:
        print(traceback.format_exc())
        return None


def extract_video_url(a_weibo):
    page_info = a_weibo.get('page_info', None)
    if page_info:
        media_info = page_info.get('media_info', None)
        if media_info:
            if media_info.get('mp4_hd_url', None):
                return media_info['mp4_hd_url']
            elif media_info.get('mp4_sd_url', None):
                return media_info['mp4_sd_url']
            else:
                print(media_info)
                sleep(10)
    return None


import pandas as pd
import os

save_folder = 'user'
if not os.path.exists(save_folder):
    os.mkdir(save_folder)


def get_commented_weibo_by_uid(uid, cookie=None):
    if cookie:
        headers['cookie'] = cookie
    else:
        raise Exception('请先修改 cookie，替换成登录后 weibo.com 的 cookie')
    print('公众号 @ 月小水长 出品')
    cur_page = 1
    result_file = os.path.join(save_folder, f'{uid}.csv')
    params = {
        'uid': uid,
        'page': '1',
        'feature': '0',
    }
    cols = ['typ', 'mid', 'publish_time', 'uid', 'screen_name', 'verified_type', 'weibo_link', 'text',
            'image_urls', 'video_url', 'region_name',
            'reposts_count', 'comments_count', 'attitudes_count']

    df = pd.DataFrame({key: [] for key in cols})
    while True:
        response = requests.get('https://weibo.com/ajax/statuses/mymblog', params=params, headers=headers)
        resp_json = response.json()
        print(resp_json)
        if resp_json['ok'] == -100:
            raise Exception('cookie 已经过期')
        data = resp_json['data']['list']
        if len(data) == 0:
            print(response.url, resp_json)
            print('\n\n data list is 0')
            break

        for item in data:
            title = item.get('title', None)
            typ = None
            if title:
                title_text = title['text']
                if '评论过的微博' in title_text:
                    typ = 'commented'
                elif '赞过的微博' in title_text:
                    typ = 'praised'
                else:
                    continue
            retweeted_status = item.get('retweeted_status', None)
            if retweeted_status:
                typ = 'reposted' + f' repost_url: https://weibo.com/{uid}/{item.get("mblogid")}'
                item = retweeted_status
                if item['user'] == None:
                    print(item['text_raw'])
                    continue

            if not typ:
                continue

            # print(typ, item)

            mid = item['mid']
            user = item['user']

            publish_time = time_formater(item['created_at'])

            uid = user['idstr']
            screen_name = user['screen_name']
            verified_type = user['verified_type']

            weibo_link = f'https://weibo.com/{uid}/{item.get("mblogid")}'

            text = item['text_raw']
            if item.get('isLongText') == True and publish_time >= '2012':
                sleep(slp_sec_per_req // 2 + 1)
                re_text = getLongText(mid)
                if re_text:
                    text = re_text

            pic_ids = item.get('pic_ids', None)
            image_urls = []
            if pic_ids:
                for pic_id in pic_ids:
                    image_urls.append(f'https://wx1.sinaimg.cn/large/{pic_id}.jpg')
            image_urls = ' '.join(image_urls)

            video_url = extract_video_url(item)

            region_name = item.get('region_name', None)

            reposts_count = item['reposts_count']
            comments_count = item['comments_count']
            attitudes_count = item['attitudes_count']

            a_weibo = {
                'typ': typ,
                'mid': mid,
                'publish_time': publish_time,
                'uid': uid,
                'screen_name': screen_name,
                'verified_type': verified_type,
                'weibo_link': weibo_link,
                'text': text,
                'image_urls': image_urls,
                'video_url': video_url,
                'region_name': region_name,
                'reposts_count': reposts_count,
                'comments_count': comments_count,
                'attitudes_count': attitudes_count
            }

            print(a_weibo)

            df = pd.concat([df, pd.DataFrame({
                key: [val] for key, val in a_weibo.items()
            })])
            df = df.append(a_weibo, ignore_index=True)

        since_id = resp_json['data']['since_id']
        cur_page += 1
        df.drop_duplicates(keep='first', subset=['weibo_link'], inplace=True)
        df.to_csv(result_file, index=False, encoding='utf-8-sig')
        print(
            f'\n\n {response.url} cur_page {cur_page} since_id {since_id} has crawled and saved {df.shape[0]} drop_duplicated '
            f'reposted or commented or praised weibo of user whose id == {uid}\n\n')
        sleep(slp_sec_per_req)
        params['since_id'] = str(since_id)
        params['page'] = str(cur_page)


### 替换成新版 weibo.com 登录后的 cookie，参考视频 https://www.bilibili.com/video/BV1934y127ZM/
cookie = 'SINAGLOBAL=替换成登录后的 cookie'
### uid 是微博用户的唯一标识，可参考链接 https://weibo-crawl-visual.buyixiao.xyz/user-guide#id
uid = '2803301701'
get_commented_weibo_by_uid(uid, cookie)
