import requests
from urllib.parse import urlencode
import time
import random
from pyquery import PyQuery as pq
import pandas as pd

# 设置代理等（新浪微博的数据是用ajax异步下拉加载的，network->xhr）
host = 'm.weibo.cn'
base_url = 'https://%s/api/container/getIndex?' % host
user_agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36'

# 设置请求头
headers = {
    'Host': host,
    # 'Referer': 'https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23%E5%A6%82%E4%BD%95%E7%9C%8B%E5%BE%85%E5%8F%8D%E5%86%85%E5%8D%B7%E7%83%AD%E6%BD%AE%23&extparam=%23%E5%A6%82%E4%BD%95%E7%9C%8B%E5%BE%85%E5%8F%8D%E5%86%85%E5%8D%B7%E7%83%AD%E6%BD%AE%23&luicode=10000011&lfid=100103type%3D38%26q%3D%E5%86%85%E5%8D%B7%26t%3D0',
    'User-Agent': user_agent
}


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
    try:
        response = requests.get(url, headers=headers)  # ,proxies=abstract_ip.get_proxy()
        if response.status_code == 200:
            return response.json()
    except:
        pass


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
global count
count = 0

'''
修改后的页面爬取解析函数
'''


def parse_page(json):
    global count
    items = json.get('data').get('cards')

    for item in items:
        try:
            topic = json.get('data').get('cardlistInfo').get('cardlist_head_cards')[0]
            topic = topic.get('head_data').get('title')
            item = item.get('mblog')
            if item:
                if item.get('isLongText') is False:  # 不是长文本
                    data = {
                        'topic': topic,
                        'id': item.get('id'),
                        'name': item.get('user').get('screen_name'),
                        'user_id': item.get('user').get('id'),
                        'sex': item.get('user').get('gender'),
                        'created': item.get('created_at'),
                        'text': pq(item.get("text")).text(),  # 仅提取内容中的文本
                        'attitudes': item.get('attitudes_count'),  # 点赞数
                        'comments': item.get('comments_count'),  # 评论数
                        'reposts': item.get('reposts_count'),  # 转发数
                        'text_Length': item.get('textLength'),
                    }
                else:  # 长文本涉及文本的展开
                    tmp = getLongText(item.get('id'))  # 调用函数
                    data = {
                        'topic': topic,
                        'id': item.get('id'),
                        'name': item.get('user').get('screen_name'),
                        'user_id': item.get('user').get('id'),
                        'sex': item.get('user').get('gender'),
                        'created': item.get('created_at'),
                        'text': tmp,  # 仅提取内容中的文本
                        'attitudes': item.get('attitudes_count'),
                        'comments': item.get('comments_count'),
                        'reposts': item.get('reposts_count'),
                        'text_Length': item.get('textLength'),

                    }

                yield data
                count += 1
        except:
            import traceback
            print(traceback.format_exc())
            pass


if __name__ == '__main__':
    keyword = '北京证券交易所'
    df = pd.DataFrame({col: [] for col in
                       ['topic', 'id', 'name', 'user_id', 'sex',
                        'created', 'text', 'attitudes', 'comments',
                        'reposts', 'text_Length']})
    for page in range(1, 500):  # 瀑布流下拉式，加载200次
        print(page)
        json = get_single_page(page, keyword)
        for result in parse_page(json):  # 需要存入的字段
            df = df.append(result, ignore_index=True)

        if page % 3 == 0:
            df.to_csv(f'{keyword}.csv', index=False, encoding='utf-8-sig')

        time.sleep(random.randint(2, 6))  # 爬取时间间隔
