# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# create_time:      2022/6/2 16:36
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# website           https://buyixiao.github.io/
# 微信公众号         月小水长

import requests

from lxml import etree


def parseResponse(response):
    html = etree.HTML(response.text)
    users = html.xpath('//div[starts-with(@class,"card card-user-b")]/div[@class="avator"]/a/@href')
    if len(users) == 0:
        return -1
    temp = users[0]
    uid = temp[temp.rindex('/') + 1:]
    return uid


def getUidByName(name):
    # https://s.weibo.com/user?q=%E6%B5%8B%E8%AF%95&Refer=weibo_user
    cookie = 'SINAGLOBAL=9725772483514.139.1613553315797; AMCV_98CF678254E93B1B0A4C98A5%40AdobeOrg=1176715910%7CMCMID%7C56647413939893769894172894748680205635%7CMCAAMLH-1652586557%7C3%7CMCAAMB-1652586557%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1651988957s%7CNONE%7CvVersion%7C5.4.0; _ga=GA1.2.648413773.1654057924; __gpi=UID=000006153f241880:T=1654057924:RT=1654057924:S=ALNI_MaR_KL_KDRNTJf3-lGlnepOdne9-A; iUUID=5e06eba520c0e063c718a5796c843783; __gads=ID=6ace8c548753e786-22d2b26ba0d300b0:T=1654057924:RT=1654057939:S=ALNI_MaX1T7rChRO-pDVp6jY21u9tt89Bw; ALF=1685596836; SCF=Ak5UIygEew_0NkA_WvuL8CBEDoRWNdgAQNITQ0vB_Z5_L61DnNwAgMbepgduKihW6ZC1Lo48jv9nZPxVWlzYZQo.; _s_tentry=weibo.com; Apache=5655623160769.916.1654065590766; ULV=1654065590826:256:2:8:5655623160769.916.1654065590766:1654056478315; UOR=,,www.google.com.hk; SSOLoginState=1654067034; SUB=_2A25Pk38KDeRhGeBG7lsQ8y3MyjWIHXVtfAFCrDV8PUJbkNAKLXHAkW1NRhjQcFQJU3-ctzoHQf04W3vlLyl6by9v; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5MCOuIe9TuswxEEPRIFh7X5NHD95Qc1h-4eKe0eh24Ws4Dqc_zi--Xi-i2iK.fi--Xi-iWiKyFi--Xi-zRiKy2i--Ri-isiKnNi--4iK.Ni-2Ri--ciKnRi-zNi--Ni-2NiKnpi--Ri-88i-2p'

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

        uid = getUidByName(row[user_name_column])
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
