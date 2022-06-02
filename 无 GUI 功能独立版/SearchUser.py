# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# create_time:      2021/10/20 22:21
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# 微信公众号         月小水长

import requests

from lxml import etree


def parseResponse(response):
    html = etree.HTML(response.text)
    users = html.xpath('//div[starts-with(@class,"card card-user-b")]/div[@class="info"]/div/a[last()-1]/@href')
    if len(users) == 0:
        return -1
    temp = users[0]
    uid = temp[temp.rindex('/') + 1:]
    return uid


def getUidByName(name):
    # https://s.weibo.com/user?q=%E6%B5%8B%E8%AF%95&Refer=weibo_user
    cookie = '复制上面的已登录的 cookie'

    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'sec-ch-ua': '"Chromium";v="94", "Google Chrome";v="94", ";Not A Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Referer': 'https://s.weibo.com/weibo?q=%E6%B5%8B%E8%AF%95',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
        'cookie': cookie
    }

    params = {
        'q': name,
        'Refer': 'weibo_user',
    }

    response = requests.get('https://s.weibo.com/user', headers=headers, params=params)

    return parseResponse(response)


def getUserLinkByName(name):
    return f"https://weibo.com/u/{getUidByName(name)}"


import pandas as pd


def dfAddUserLink(file_path, user_name_column, user_link_column='user_link', finish_column='finish'):
    df = pd.read_csv(file_path)
    if not finish_column in df.columns.values.tolist():
        df[finish_column] = [False for _ in range(df.shape[0])]
        df[user_link_column] = ['' for _ in range(df.shape[0])]
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

    consist = 0
    consist_limit = 3
    for index, row in df.iterrows():
        print(f'{index+1}/{df.shape[0]}')
        if row[finish_column] == True:
            continue

        uid = getUidByName(row[user_name_cloumn])
        if uid == -1:
            consist += 1
            if consist >= consist_limit:
                print('请检查是否需要换 cookie')
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                break
        else:
            consist = 0
        user_link = f"https://weibo.com/u/{uid}"
        print(user_link)

        df.loc[index, user_link_column] = user_link
        df.loc[index, finish_column] = True
        if index % 10 == 0:
            df.to_csv(file_path, index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    userLink = getUserLinkByName('水哥')
    print(userLink)
    dfAddUserLink('test.csv', user_name_column='user_name')
