import requests
from urllib.parse import urlencode
import time
import random
from pyquery import PyQuery as pq

# 设置代理等（新浪微博的数据是用ajax异步下拉加载的，network->xhr）
host = 'm.weibo.cn'
base_url = 'https://%s/api/container/getIndex?' % host
user_agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36'

# 设置请求头
headers = {
    'Host': host,
    'keep': 'close',
    # 'Referer': 'https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23%E5%A6%82%E4%BD%95%E7%9C%8B%E5%BE%85%E5%8F%8D%E5%86%85%E5%8D%B7%E7%83%AD%E6%BD%AE%23&extparam=%23%E5%A6%82%E4%BD%95%E7%9C%8B%E5%BE%85%E5%8F%8D%E5%86%85%E5%8D%B7%E7%83%AD%E6%BD%AE%23&luicode=10000011&lfid=100103type%3D38%26q%3D%E5%86%85%E5%8D%B7%26t%3D0',
    'User-Agent': user_agent
}

save_per_n_page = 10

from datetime import datetime


def time_formater(input_time_str):
    input_format = '%a %b %d %H:%M:%S %z %Y'
    output_format = '%Y-%m-%d %H:%M:%S'

    return datetime.strptime(input_time_str, input_format).strftime(output_format)


# 按页数抓取数据
def get_single_page(page, keyword):
    # 请求参数
    params = {
        'containerid': f'100103type=1&q=#{keyword}#',  # 、、教育内卷、职场内卷、如何看待内卷的社会状态、如何避免婚姻内卷、
        'page_type': 'searchall',
        'page': page
    }
    url = base_url + urlencode(params)
    print(url)
    error_times = 3
    while True:
        response = requests.get(url, headers=headers)  # ,proxies=abstract_ip.get_proxy()
        if response.status_code == 200:
            if len(response.json().get('data').get('cards')) > 0:
                return response.json()
        time.sleep(3)
        error_times += 1
        # 连续出错次数超过 3
        if error_times > 3:
            return None


# 长文本爬取代码段
def getLongText(lid):  # lid为长文本对应的id
    # 长文本请求头
    headers_longtext = {
        'Host': host,
        'Referer': 'https://m.weibo.cn/status/' + lid,
        'User-Agent': user_agent
    }
    params = {
        'id': lid
    }
    url = 'https://m.weibo.cn/statuses/extend?' + urlencode(params)
    try:
        response = requests.get(url, headers=headers_longtext)  # proxies=abstract_ip.get_proxy()
        if response.status_code == 200:  # 数据返回成功
            jsondata = response.json()
            tmp = jsondata.get('data')
            return pq(tmp.get("longTextContent")).text()  # 解析返回结构，获取长文本对应内容
    except:
        pass


# 解析页面返回的json数据
count = 0

'''
修改后的页面爬取解析函数
'''


def parse_page(json_data):
    global count
    items = json_data.get('data').get('cards')

    for index, item in enumerate(items):
        if item.get('card_type') == 7:
            print('导语')
            continue
        # topic = json_data.get('data').get('cardlistInfo').get('cardlist_head_cards')[0]
        # # 单独的关键词抓取不是超话，会有 topic == null
        # if topic is None or topic.get('head_data', None) is None:
        #     topic = keyword
        # else:
        #     topic = topic.get('head_data').get('title')
        item = item.get('mblog') if item.get('mblog') else item.get('card_group')[0].get('mblog')
        if item:
            if item.get('isLongText') is False:  # 不是长文本
                data = {
                    'wid': item.get('id'),
                    'user_name': item.get('user').get('screen_name'),
                    'user_id': item.get('user').get('id'),
                    'gender': item.get('user').get('gender'),
                    'publish_time': time_formater(item.get('created_at')),
                    'text': pq(item.get("text")).text(),  # 仅提取内容中的文本
                    'like_count': item.get('attitudes_count'),  # 点赞数
                    'comment_count': item.get('comments_count'),  # 评论数
                    'forward_count': item.get('reposts_count'),  # 转发数
                }
            else:  # 长文本涉及文本的展开
                tmp = getLongText(item.get('id'))  # 调用函数
                data = {
                    'wid': item.get('id'),
                    'user_name': item.get('user').get('screen_name'),
                    'user_id': item.get('user').get('id'),
                    'gender': item.get('user').get('gender'),
                    'publish_time': time_formater(item.get('created_at')),
                    'text': tmp,  # 仅提取内容中的文本
                    'like_count': item.get('attitudes_count'),
                    'comment_count': item.get('comments_count'),
                    'forward_count': item.get('reposts_count'),
                }
            count += 1
            print(f'total count: {count}')
            yield data


import os, csv

if __name__ == '__main__':
    keyword = '北京疫情'
    result_file = f'{keyword}.csv'
    if not os.path.exists(result_file):
        with open(result_file, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['wid', 'user_name', 'user_id', 'gender',
                             'publish_time', 'text', 'like_count', 'comment_count',
                             'forward_count'])

    temp_data = []

    empty_times = 0

    for page in range(1, 50000):  # 瀑布流下拉式，加载
        print(f'page: {page}')
        json_data = get_single_page(page, keyword)
        if json_data == None:
            print('json is none')
            break

        if len(json_data.get('data').get('cards')) <= 0:
            empty_times += 1
        else:
            empty_times = 0
        if empty_times > 3:
            print('\n\n consist empty over 3 times \n\n')
            break

        for result in parse_page(json_data):  # 需要存入的字段
            temp_data.append(result)
        if page % save_per_n_page == 0:
            with open(result_file, mode='a+', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                for d in temp_data:
                    writer.writerow(
                        [d['wid'], d['user_name'], d['user_id'], d['gender'],
                         d['publish_time'], d['text'], d['like_count'], d['comment_count'],
                         d['forward_count']])
            print(f'\n\n------cur turn write {len(temp_data)} rows to csv------\n\n')
            temp_data = []
        time.sleep(random.randint(2, 6))  # 爬取时间间隔
