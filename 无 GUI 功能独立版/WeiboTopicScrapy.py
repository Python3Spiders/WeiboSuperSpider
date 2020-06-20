# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# pc_type           lenovo
# create_time:      2020/1/12 22:04
# file_name:        main.py
# github            https://github.com/inspurer
# qq邮箱            2391527690@qq.com
# 微信公众号         月小水长(ID: inspurer)


import requests

from lxml import etree
from collections import OrderedDict

from urllib.parse import quote

import csv

import traceback

import random

import re

from time import sleep

import os

from datetime import datetime, timedelta
import sys
from threading import Thread

Cookie = '''改成你自己的 cookie'''

User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'


class WeiboTopicScrapy(Thread):

    def __init__(self,keyword,filter,start_time,end_time):
        Thread.__init__(self)
        self.headers={
            'Cookie':Cookie,
            'User_Agent':User_Agent
        }
        self.keyword = keyword
        self.filter = filter # 1: 原创微博； 0：所有微博
        self.start_time = start_time
        self.end_time = end_time
        self.got_num = 0  # 爬取到的微博数
        self.weibo = []  # 存储爬取到的所有微博信息
        if not os.path.exists('topic'):
            os.mkdir('topic')
        self.start()

    def deal_html(self,url):
        """处理html"""
        try:
            html = requests.get(url, headers=self.headers).content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def deal_garbled(self,info):
        """处理乱码"""
        try:
            info = (info.xpath('string(.)').replace(u'\u200b', '').encode(
                sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
            return info
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_long_weibo(self,weibo_link):
        """获取长原创微博"""
        try:
            selector = self.deal_html(weibo_link)
            info = selector.xpath("//div[@class='c']")[1]
            wb_content = self.deal_garbled(info)
            wb_time = info.xpath("//span[@class='ct']/text()")[0]
            weibo_content = wb_content[wb_content.find(':') +
                                       1:wb_content.rfind(wb_time)]
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_original_weibo(self,info, weibo_id):
        """获取原创微博"""
        try:
            weibo_content = self.deal_garbled(info)
            weibo_content = weibo_content[:weibo_content.rfind(u'赞')]
            a_text = info.xpath('div//a/text()')
            if u'全文' in a_text:
                weibo_link = 'https://weibo.cn/comment/' + weibo_id
                wb_content = self.get_long_weibo(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_long_retweet(self,weibo_link):
        """获取长转发微博"""
        try:
            wb_content = self.get_long_weibo(weibo_link)
            weibo_content = wb_content[:wb_content.rfind('原文转发')]
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_retweet(self,info, weibo_id):
        """获取转发微博"""
        try:
            original_user = info.xpath("div/span[@class='cmt']/a/text()")
            if not original_user:
                wb_content = '转发微博已被删除'
                return wb_content
            else:
                original_user = original_user[0]
            wb_content = self.deal_garbled(info)
            wb_content = wb_content[wb_content.find(':') +
                                    1:wb_content.rfind('赞')]
            wb_content = wb_content[:wb_content.rfind('赞')]
            a_text = info.xpath('div//a/text()')
            if '全文' in a_text:
                weibo_link = 'https://weibo.cn/comment/' + weibo_id
                weibo_content = self.get_long_retweet(weibo_link)
                if weibo_content:
                    wb_content = weibo_content
            retweet_reason = self.deal_garbled(info.xpath('div')[-1])
            retweet_reason = retweet_reason[:retweet_reason.rindex('赞')]
            wb_content = (retweet_reason + '\n' + '原始用户: ' + original_user +
                          '\n' + '转发内容: ' + wb_content)
            return wb_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_weibo_content(self,info, is_original):
        """获取微博内容"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            if is_original:
                weibo_content = self.get_original_weibo(info, weibo_id)
            else:
                weibo_content = self.get_retweet(info, weibo_id)
            print(weibo_content)
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_place(self,info):
        """获取微博发布位置"""
        try:
            div_first = info.xpath('div')[0]
            a_list = div_first.xpath('a')
            publish_place = '无'
            for a in a_list:
                if ('place.weibo.com' in a.xpath('@href')[0]
                        and a.xpath('text()')[0] == '显示地图'):
                    weibo_a = div_first.xpath("span[@class='ctt']/a")
                    if len(weibo_a) >= 1:
                        publish_place = weibo_a[-1]
                        if ('视频' == div_first.xpath(
                                "span[@class='ctt']/a/text()")[-1][-2:]):
                            if len(weibo_a) >= 2:
                                publish_place = weibo_a[-2]
                            else:
                                publish_place = '无'
                        publish_place = self.deal_garbled(publish_place)
                        break
            print('微博发布位置: ' + publish_place)
            return publish_place
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_time(self,info):
        """获取微博发布时间"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            publish_time = str_time.split('来自')[0]
            if '刚刚' in publish_time:
                publish_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            elif '分钟' in publish_time:
                minute = publish_time[:publish_time.find('分钟')]
                minute = timedelta(minutes=int(minute))
                publish_time = (datetime.now() -
                                minute).strftime('%Y-%m-%d %H:%M')
            elif '今天' in publish_time:
                today = datetime.now().strftime('%Y-%m-%d')
                time = publish_time[3:]
                publish_time = today + ' ' + time
            elif '月' in publish_time:
                year = datetime.now().strftime('%Y')
                month = publish_time[0:2]
                day = publish_time[3:5]
                time = publish_time[7:12]
                publish_time = year + '-' + month + '-' + day + ' ' + time
            else:
                publish_time = publish_time[:16]
            print('微博发布时间: ' + publish_time)
            return publish_time
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_tool(self,info):
        """获取微博发布工具"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            if len(str_time.split('来自')) > 1:
                publish_tool = str_time.split(u'来自')[1]
            else:
                publish_tool = '无'
            print('微博发布工具: ' + publish_tool)
            return publish_tool
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_weibo_footer(self,info):
        """获取微博点赞数、转发数、评论数"""
        try:
            footer = {}
            pattern = r'\d+'
            str_footer = info.xpath('div')[-1]
            str_footer = self.deal_garbled(str_footer)
            str_footer = str_footer[str_footer.rfind('赞'):]
            weibo_footer = re.findall(pattern, str_footer, re.M)

            up_num = int(weibo_footer[0])
            print('点赞数: ' + str(up_num))
            footer['up_num'] = up_num

            retweet_num = int(weibo_footer[1])
            print('转发数: ' + str(retweet_num))
            footer['retweet_num'] = retweet_num

            comment_num = int(weibo_footer[2])
            print('评论数: ' + str(comment_num))
            footer['comment_num'] = comment_num
            return footer
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def extract_picture_urls(self,info, weibo_id):
        print('开始提取图片 URL')
        """提取微博原始图片url"""
        try:
            a_list = info.xpath('./div/a/@href')
            all_pic = 'https://weibo.cn/mblog/picAll/' + weibo_id + '?rl=1'
            if all_pic in a_list:
                selector = self.deal_html(all_pic)
                preview_picture_list = selector.xpath('//img/@src')
                picture_list = [
                        p.replace('/thumb180/', '/large/')
                        for p in preview_picture_list
                ]
                picture_urls = ','.join(picture_list)
                print(picture_urls)
            else:
                picture_urls = '无'
                if info.xpath('.//img/@src'):
                    preview_picture = info.xpath('.//img/@src')[-1]
                    picture_urls = preview_picture.replace(
                            '/wap180/', '/large/')
                else:
                    sys.exit(
                            "爬虫微博可能被设置成了'不显示图片'，请前往"
                            "'https://weibo.cn/account/customize/pic'，修改为'显示'"
                    )
            return picture_urls
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_picture_urls(self,info, is_original):
        """获取微博原始图片url"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            picture_urls = {}
            if is_original:
                original_pictures = self.extract_picture_urls(info, weibo_id)
                picture_urls['original_pictures'] = original_pictures
                if not self.filter:
                    picture_urls['retweet_pictures'] = '无'
            else:
                retweet_url = info.xpath("div/a[@class='cc']/@href")[0]
                retweet_id = retweet_url.split('/')[-1].split('?')[0]
                retweet_pictures = self.extract_picture_urls(info, retweet_id)
                picture_urls['retweet_pictures'] = retweet_pictures
                a_list = info.xpath('div[last()]/a/@href')
                original_picture = '无'
                for a in a_list:
                    if a.endswith(('.gif', '.jpeg', '.jpg', '.png')):
                        original_picture = a
                        break
                picture_urls['original_pictures'] = original_picture
            return picture_urls
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publisher_info(self, link):
        response = requests.get(url=link, headers=self.headers)
        html = self.deal_html(link)
        user_info = html.xpath('//div[@class="ut"]/span[@class="ctt"]')[0]
        user_info = user_info.xpath('string(.)').strip()
        # 去掉  \xa0
        user_info = ' '.join(user_info.split())
        kindex = user_info.index(' ')
        username = user_info[:kindex]
        sex = user_info[kindex + 1:user_info.index('/')]
        province = user_info[user_info.index('/') + 1:user_info.rindex(' ')]

        following = html.xpath('//div[@class="tip2"]/a[1]/text()')[0]
        following = following[3:-1]
        followd = html.xpath('//div[@class="tip2"]/a[2]/text()')[0]
        followd = followd[3:-1]
        # print(link, followd)
        return username, sex, province, following, followd

    def get_one_weibo(self,info):
        """获取一条微博的全部信息"""
        try:
            weibo = OrderedDict()
            is_original = False if len(info.xpath("div/span[@class='cmt']")) > 3 else True
            if (not self.filter) or is_original:
                weibo['id'] = info.xpath('@id')[0][2:]
                # weibo['publisher'] = info.xpath('div/a/text()')[0]
                publisher_link = info.xpath('div/a/@href')[0]

                weibo['publisher_name'],weibo['publisher_sex'], weibo['publisher_province'],\
                    weibo['publisher_following'], weibo['publisher_followed'] = self.get_publisher_info(publisher_link)

                weibo['content'] = self.get_weibo_content(info,
                                                     is_original)  # 微博内容
                picture_urls = self.get_picture_urls(info, is_original)
                weibo['original_pictures'] = picture_urls[
                    'original_pictures']  # 原创图片url
                if not self.filter:
                    weibo['retweet_pictures'] = picture_urls[
                        'retweet_pictures']  # 转发图片url
                    weibo['original'] = is_original  # 是否原创微博
                weibo['publish_place'] = self.get_publish_place(info)  # 微博发布位置
                weibo['publish_time'] = self.get_publish_time(info)  # 微博发布时间
                weibo['publish_tool'] = self.get_publish_tool(info)  # 微博发布工具
                footer = self.get_weibo_footer(info)
                weibo['up_num'] = footer['up_num']  # 微博点赞数
                weibo['retweet_num'] = footer['retweet_num']  # 转发数
                weibo['comment_num'] = footer['comment_num']  # 评论数
            else:
                weibo = None
            return weibo
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def write_csv(self, wrote_num):
        """将爬取的信息写入csv文件"""
        try:
            result_headers = [
                '微博id',
                '发布者昵称',
                '发布者性别',
                '发布者地区',
                '发布者关注数',
                '发布者粉丝数',
                '微博正文',
                '原始图片url',
                '发布位置',
                '发布时间',
                '发布工具',
                '点赞数',
                '转发数',
                '评论数',
            ]
            if not self.filter:
                result_headers.insert(8, '被转发微博原始图片url')
                result_headers.insert(9, '是否为原创微博')
            result_data = [w.values() for w in self.weibo][wrote_num:]

            with open('topic/'+self.keyword+'.csv', 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                if wrote_num == 0:
                    writer.writerows([result_headers])
                writer.writerows(result_data)
            print('%d条微博写入csv文件完毕:' % self.got_num)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()


    def run(self):

        wrote_num = 0
        page1 = 0
        random_pages = random.randint(1, 5)
        pageNum = 1000000

        for page in range(1, pageNum):
            print('\n\n第{}页....\n'.format(page))
            Referer = 'https://weibo.cn/search/mblog?hideSearchFrame=&keyword={}&page={}'.format(quote(self.keyword),
                                                                                                 page - 1)
            headers = {
                'Cookie': Cookie,
                'User-Agent': User_Agent,
                'Referer': Referer
            }
            params = {
                'hideSearchFrame': '',
                'keyword': self.keyword,
                'advancedfilter': '1',
                'starttime': self.start_time,
                'endtime': self.end_time,
                'sort': 'time',
                'page': page
            }
            res = requests.get(url='https://weibo.cn/search/mblog', params=params, headers=headers)

            html = etree.HTML(res.text.encode('utf-8'))

            try:
                weibos = html.xpath("//div[@class='c' and @id]")

                for i in range(0, len(weibos)):

                    aweibo = self.get_one_weibo(info=weibos[i])
                    if aweibo:
                        self.weibo.append(aweibo)
                        self.got_num += 1
                        print('-' * 100)

                if page % 3 == 0 and self.got_num>wrote_num:  # 每爬3页写入一次文件
                    self.write_csv(wrote_num)
                    wrote_num = self.got_num

                # 通过加入随机等待避免被限制。爬虫速度过快容易被系统限制(一段时间后限
                # 制会自动解除)，加入随机等待模拟人的操作，可降低被系统限制的风险。默
                # 认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间
                if page - page1 == random_pages and page < pageNum:
                    sleep(random.randint(6, 10))
                    page1 = page
                    # random_pages = random.randint(1, 5)
                    random_pages = random.randint(1, 3)

            except:
                print(res.text)

        if self.got_num > wrote_num:
            self.write_csv(wrote_num)  # 将剩余不足3页的微博写入文件
        if not self.filter:
            print('共爬取' + str(self.got_num) + '条微博')
        else:
            print('共爬取' + str(self.got_num) + '条原创微博')

if __name__ == '__main__':
    #filter = 0 爬取所有微博，filter = 1 爬取原创微博
    keyword = '北京疫情'
    WeiboTopicScrapy(keyword=keyword, filter=1, start_time='2020601', end_time='20200620')
