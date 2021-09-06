# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# create_time:      2021/9/3 21:01
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# 微信公众号         月小水长

import requests

import pandas as pd

from time import sleep

import json

headers = {
    'authority': 'weibo.com',
    'x-requested-with': 'XMLHttpRequest',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'content-type': 'application/x-www-form-urlencoded',
    'accept': '*/*',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://weibo.com/1192329374/KnnG78Yf3?filter=hot&root_comment_id=0&type=comment',
    'accept-language': 'zh-CN,zh;q=0.9,en-CN;q=0.8,en;q=0.7,es-MX;q=0.6,es;q=0.5',
    'cookie': '介里，患曲奇'
}


def parseUid(uid):
    response = requests.get(url=f'https://weibo.com/ajax/profile/info?custom={uid}', headers=headers)
    try:
        return response.json()['data']['user']['id']
    except:
        return None


def getUserInfo(uid):
    try:
        uid = int(uid)
    except:
        # 说明是 xiena 这样的英文串
        uid = parseUid(uid)
        if not uid:
            return None
    response = requests.get(url=f'https://weibo.com/ajax/profile/detail?uid={uid}', headers=headers)
    if response.status_code == 400:
        return {
            'errorMsg': '用户可能注销或者封号'
        }
    resp_json = response.json().get('data', None)
    if not resp_json:
        return None
    sunshine_credit = resp_json.get('sunshine_credit', None)
    if sunshine_credit:
        sunshine_credit_level = sunshine_credit.get('level', None)
    else:
        sunshine_credit_level = None
    education = resp_json.get('education', None)
    if education:
        school = education.get('school', None)
    else:
        school = None

    location = resp_json.get('location', None)
    gender = resp_json.get('gender', None)

    birthday = resp_json.get('birthday', None)
    created_at = resp_json.get('created_at', None)
    description = resp_json.get('description', None)
    # 我关注的人中有多少人关注 ta
    followers = resp_json.get('followers', None)
    if followers:
        followers_num = followers.get('total_number', None)
    else:
        followers_num = None
    return {
        'sunshine_credit_level': sunshine_credit_level,
        'school': school,
        'location': location,
        'gender': gender,
        'birthday': birthday,
        'created_at': created_at,
        'description': description,
        'followers_num': followers_num
    }

'''
给 df 加 user_info
'''


def dfAddUserInfo(file_path, user_col, user_info_col='user_info'):
    '''
    @params file_path 指定路径
    @params user_col 指定用户主页链接在那一列, 比如评论csv文件的是 comment_user_link
    @params user_info_col 指定新加的 userinfo 列名，默认是 user_info
    '''
    df = pd.read_csv(file_path)
    user_info_init_value = 'init'
    columns = df.columns.values.tolist()
    if not user_info_col in columns:
        df[user_info_col] = [user_info_init_value for _ in range(df.shape[0])]
    for index, row in df.iterrows():
        print(f'   {index+1}/{df.shape[0]}   ')
        if not row.get(user_info_col, user_info_init_value) is user_info_init_value:
            print('skip')
            continue
        user_link = row[user_col]
        user_id = user_link[user_link.rindex('/')+1:]
        user_info = getUserInfo(user_id)
        print(user_info)
        if user_info:
            # 在 user_info 中统一为 user_link
            user_info['user_link'] = user_link
            df.loc[index, user_info_col] = json.dumps(user_info)
            sleep(1)
        else:
            print(user_link)
            break
    df.to_csv(file_path, index=False, encoding='utf-8-sig')

'''
从已经加好 userinfo 的 df 里遍历 userinfo 
'''
def dfGetUserInfo(file_path, user_info_col):
    df = pd.read_csv(file_path)
    for index, row in df.iterrows():
        user_info = json.loads(row[user_info_col])
        location = user_info['location']
        user_link = user_info['user_link']

        print(location, user_link)


if __name__ == '__main__':
    user_info = getUserInfo(uid='xiena')
    print(user_info)

    dfAddUserInfo(file_path='KnnG78Yf3.csv', user_col='comment_user_link')
    dfGetUserInfo(file_path='KnnG78Yf3.csv', user_info_col='user_info')
