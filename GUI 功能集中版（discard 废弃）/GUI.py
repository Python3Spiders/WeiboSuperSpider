# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# pc_type           lenovo
# create_time:      2019/8/13 15:06
# file_name:        GUI.py
# github            https://github.com/inspurer
# qq邮箱            2391527690@qq.com
# 微信公众号         月小水长(ID: inspurer)

# ff2941


from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, qApp,QListView,QInputDialog,\
    QMessageBox,QProgressDialog,QDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import (pyqtSignal, QObject,QEvent,Qt)

from MyDialog import MyDialog

from urllib.parse import quote
from ListView import ListView,vgs
import webbrowser
from threading import Thread
import json

import csv
import os
import random
import re
import sys
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from time import sleep

import requests
requests.packages.urllib3.disable_warnings()
from lxml import etree

filter = 1

Cookie = '''替换成你自己的 cookie'''
User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'

headers = {
    'user-agent':User_Agent,
    'Cookie': Cookie
}


class WeiboSearchScrapy(Thread):

    def __init__(self,keyword):
        global headers
        Thread.__init__(self)
        self.headers = headers
        self.keyword = keyword
        self.daemon = True
        self.start()

    def run(self):
        global ss
        query_data = {
            'keyword': self.keyword,
            'suser': '找人'
        }

        try:
            search_response = requests.post(url='https://weibo.cn/search/?pos=search', headers=self.headers, data=query_data,verify=False)

            search_html = etree.HTML(search_response.text.encode('utf-8'))

            print(search_response.text)

            tables = search_html.xpath('/html/body/table')  # 返回一个列表
            for i, table in enumerate(tables):
                href = search_html.xpath('/html/body/table[{}]/tr/td[1]/a/@href'.format(i + 1))[0]

                info_response = requests.get(url='https://weibo.cn{}'.format(href), headers=self.headers,verify=False)

                info_html = etree.HTML(info_response.text.encode('utf-8'))

                # # 如果自己的微博出现在搜索列表,会报错
                # print(info_html)

                avatar_url = info_html.xpath('//table/tr/td[1]/a/img/@src')[0]

                uid = info_html.xpath('//table/tr/td[1]/a/@href')[0]
                uid = uid[1:uid.rindex('/')]

                nick_name = info_html.xpath('//table/tr/td[2]/div/span[1]/text()')[0]

                if "/" in nick_name:
                    nick_name = nick_name[0:nick_name.index("/") - 2]

                print(avatar_url, uid, nick_name, '\n\n\n\n\n')

                with open("{}.jpg".format(i), "wb") as f:
                    f.write(requests.get(avatar_url,verify=False).content)

                item_data = {'rank': str(i + 1), 'name': nick_name, 'iconPath': "{}.jpg".format(i), 'uid': uid}

                ss.ps.emit(json.dumps(item_data))
            ss.ps.emit('EOF')
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

class WeiboUserScrapy(Thread):

    def __init__(self, user_id, filter=0):
        global headers
        Thread.__init__(self)
        self.headers = headers

        if filter != 0 and filter != 1:
            sys.exit('filter值应为0或1,请重新输入')

        self.user_id = user_id  # 用户id,即需要我们输入的数字,如昵称为"Dear-迪丽热巴"的id为1669879400
        self.filter = filter  # 取值范围为0、1,程序默认值为0,代表要爬取用户的全部微博,1代表只爬取用户的原创微博
        self.nickname = ''  # 用户昵称,如“Dear-迪丽热巴”
        self.weibo_num = 0  # 用户全部微博数
        self.got_num = 0  # 爬取到的微博数
        self.following = 0  # 用户关注数
        self.followers = 0  # 用户粉丝数
        self.weibo = []  # 存储爬取到的所有微博信息
        self.start()

    def deal_html(self, url):
        """处理html"""
        try:
            html = requests.get(url, headers=self.headers,verify=False).content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def deal_garbled(self, info):
        """处理乱码"""
        try:
            info = (info.xpath('string(.)').replace(u'\u200b', '').encode(
                sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
            return info
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_nickname(self):
        """获取用户昵称"""
        try:
            url = 'https://weibo.cn/{}/info'.format(self.user_id)
            selector = self.deal_html(url)
            nickname = selector.xpath('//title/text()')[0]
            self.nickname = nickname[:-3]
            if self.nickname == '登录 - 新' or self.nickname == '新浪':
                sys.exit('cookie错误或已过期')
            print('用户昵称: ' + self.nickname)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_user_info(self, selector):
        """获取用户昵称、微博数、关注数、粉丝数"""
        try:
            self.get_nickname()  # 获取用户昵称
            user_info = selector.xpath("//div[@class='tip2']/*/text()")

            self.weibo_num = int(user_info[0][3:-1])
            print('微博数: ' + str(self.weibo_num))

            self.following = int(user_info[1][3:-1])
            print('关注数: ' + str(self.following))

            self.followers = int(user_info[2][3:-1])
            print('粉丝数: ' + str(self.followers))
            print('*' * 100)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_page_num(self, selector):
        """获取微博总页数"""
        try:
            if selector.xpath("//input[@name='mp']") == []:
                page_num = 1
            else:
                page_num = (int)(
                    selector.xpath("//input[@name='mp']")[0].attrib['value'])
            return page_num
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_long_weibo(self, weibo_link):
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

    def get_original_weibo(self, info, weibo_id):
        """获取原创微博"""
        try:
            weibo_content = self.deal_garbled(info)
            weibo_content = weibo_content[:weibo_content.rfind('赞')]
            a_text = info.xpath('div//a/text()')
            if '全文' in a_text:
                weibo_link = 'https://weibo.cn/comment/' + weibo_id
                wb_content = self.get_long_weibo(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_long_retweet(self, weibo_link):
        """获取长转发微博"""
        try:
            wb_content = self.get_long_weibo(weibo_link)
            weibo_content = wb_content[:wb_content.rfind('原文转发')]
            return weibo_content
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_retweet(self, info, weibo_id):
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

    def is_original(self, info):
        """判断微博是否为原创微博"""
        is_original = info.xpath("div/span[@class='cmt']")
        if len(is_original) > 3:
            return False
        else:
            return True

    def get_weibo_content(self, info, is_original):
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

    def get_publish_place(self, info):
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
                                publish_place = u'无'
                        publish_place = self.deal_garbled(publish_place)
                        break
            print('微博发布位置: ' + publish_place)
            return publish_place
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_publish_time(self, info):
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

    def get_publish_tool(self, info):
        """获取微博发布工具"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            if len(str_time.split('来自')) > 1:
                publish_tool = str_time.split('来自')[1]
            else:
                publish_tool = '无'
            print('微博发布工具: ' + publish_tool)
            return publish_tool
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_weibo_footer(self, info):
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

    def extract_picture_urls(self, info, weibo_id):
        """提取微博原始图片url"""
        try:
            a_list = info.xpath('div/a/@href')
            first_pic = 'https://weibo.cn/mblog/pic/' + weibo_id + '?rl=0'
            all_pic = 'https://weibo.cn/mblog/picAll/' + weibo_id + '?rl=1'
            if first_pic in a_list:
                if all_pic in a_list:
                    selector = self.deal_html(all_pic)
                    preview_picture_list = selector.xpath('//img/@src')
                    picture_list = [
                        p.replace('/thumb180/', '/large/')
                        for p in preview_picture_list
                    ]
                    picture_urls = ','.join(picture_list)
                else:
                    if info.xpath('.//img/@src'):
                        preview_picture = info.xpath('.//img/@src')[-1]
                        picture_urls = preview_picture.replace(
                            '/wap180/', '/large/')
                    else:
                        sys.exit(
                            "爬虫微博可能被设置成了'不显示图片'，请前往"
                            "'https://weibo.cn/account/customize/pic'，修改为'显示'"
                        )
            else:
                picture_urls = '无'
            return picture_urls
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_picture_urls(self, info, is_original):
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

    def get_one_weibo(self, info):
        """获取一条微博的全部信息"""
        try:
            weibo = OrderedDict()
            is_original = self.is_original(info)
            if (not self.filter) or is_original:
                weibo['id'] = info.xpath('@id')[0][2:]
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

    def get_one_page(self, page):
        """获取第page页的全部微博"""
        try:
            url = 'https://weibo.cn/u/%d?page=%d' % (self.user_id, page)
            selector = self.deal_html(url)
            info = selector.xpath("//div[@class='c']")
            is_exist = info[0].xpath("div/span[@class='ctt']")
            if is_exist:
                for i in range(0, len(info) - 2):
                    weibo = self.get_one_weibo(info[i])
                    if weibo:
                        self.weibo.append(weibo)
                        self.got_num += 1
                        print('-' * 100)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def get_filepath(self, type):
        """获取结果文件路径"""
        try:
            file_dir = os.path.split(os.path.realpath(
                __file__))[0] + os.sep + 'user' + os.sep + self.nickname
            if type == 'img':
                file_dir = file_dir + os.sep + 'img'
            if not os.path.isdir(file_dir):
                os.makedirs(file_dir)
            if type == 'img':
                return file_dir
            file_path = file_dir + os.sep + '%d' % self.user_id + '.' + type
            return file_path
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def write_csv(self, wrote_num):
        """将爬取的信息写入csv文件"""
        try:
            result_headers = [
                '微博id',
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
                result_headers.insert(3, '被转发微博原始图片url')
                result_headers.insert(4, '是否为原创微博')
            result_data = [w.values() for w in self.weibo][wrote_num:]

            with open(self.get_filepath('csv'),'a',encoding='utf-8-sig',newline='') as f:
                writer = csv.writer(f)
                if wrote_num == 0:
                    writer.writerows([result_headers])
                writer.writerows(result_data)
            print(u'%d条微博写入csv文件完毕,保存路径:' % self.got_num)
            print(self.get_filepath('csv'))
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def write_txt(self, wrote_num):
        """将爬取的信息写入txt文件"""
        try:
            temp_result = []
            if wrote_num == 0:
                if self.filter:
                    result_header = '\n\n原创微博内容: \n'
                else:
                    result_header = '\n\n微博内容: \n'
                result_header = ('用户信息\n用户昵称：' + self.nickname + '\n用户id: ' +
                                 str(self.user_id) + '\n微博数: ' +
                                 str(self.weibo_num) + '\n关注数: ' +
                                 str(self.following) + '\n粉丝数: ' +
                                 str(self.followers) + result_header)
                temp_result.append(result_header)
            for i, w in enumerate(self.weibo[wrote_num:]):
                temp_result.append(
                    str(wrote_num + i + 1) + ':' + w['content'] + '\n' +
                    '微博位置: ' + w['publish_place'] + '\n' + '发布时间: ' +
                    w['publish_time'] + '\n' + '点赞数: ' + str(w['up_num']) +
                    '   转发数: ' + str(w['retweet_num']) + '   评论数: ' +
                    str(w['comment_num']) + '\n' + '发布工具: ' +
                    w['publish_tool'] + '\n\n')
            result = ''.join(temp_result)
            with open(self.get_filepath('txt'), 'ab') as f:
                f.write(result.encode(sys.stdout.encoding))
            print('%d条微博写入txt文件完毕,保存路径:' % self.got_num)
            print(self.get_filepath('txt'))
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def write_file(self, wrote_num):
        """写文件"""
        if self.got_num > wrote_num:
            self.write_csv(wrote_num)
            self.write_txt(wrote_num)

    def get_weibo_info(self):
        global us
        """获取微博信息"""
        try:
            url = 'https://weibo.cn/u/%d' % (self.user_id)
            selector = self.deal_html(url)
            self.get_user_info(selector)  # 获取用户昵称、微博数、关注数、粉丝数
            page_num = self.get_page_num(selector)  # 获取微博总页数
            us.ps.emit('start',page_num)
            wrote_num = 0
            page1 = 0
            random_pages = random.randint(1, 5)
            for page in range(1, page_num + 1):
                self.get_one_page(page)  # 获取第page页的全部微博

                us.ps.emit('run', page)

                if page % 3 == 0:  # 每爬3页写入一次文件
                    self.write_file(wrote_num)
                    wrote_num = self.got_num

                # 通过加入随机等待避免被限制。爬虫速度过快容易被系统限制(一段时间后限
                # 制会自动解除)，加入随机等待模拟人的操作，可降低被系统限制的风险。默
                # 认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间
                if page - page1 == random_pages and page < page_num:
                    sleep(random.randint(6, 10))
                    page1 = page
                    random_pages = random.randint(1, 5)
            self.write_file(wrote_num)  # 将剩余不足3页的微博写入文件
            if not self.filter:
                print('共爬取' + str(self.got_num) + '条微博')
            else:
                print('共爬取' + str(self.got_num) + '条原创微博')
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def run(self):
        """运行爬虫"""
        try:
            self.get_weibo_info()
            print('信息抓取完毕')
            print('*' * 100)

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

class WeiboTopicScrapy(Thread):

    def __init__(self,keyword,filter,limit_date):
        Thread.__init__(self)
        self.headers={
            'Cookie':Cookie,
            'User_Agent':User_Agent
        }
        self.keyword = keyword
        self.filter = filter # 1: 原创微博； 0：所有微博
        self.limit_date = limit_date
        self.flag = True
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
        """提取微博原始图片url"""
        try:
            a_list = info.xpath('div/a/@href')
            first_pic = 'https://weibo.cn/mblog/pic/' + weibo_id + '?rl=0'
            all_pic = 'https://weibo.cn/mblog/picAll/' + weibo_id + '?rl=1'
            if first_pic in a_list:
                if all_pic in a_list:
                    selector = self.deal_html(all_pic)
                    preview_picture_list = selector.xpath('//img/@src')
                    picture_list = [
                        p.replace('/thumb180/', '/large/')
                        for p in preview_picture_list
                    ]
                    picture_urls = ','.join(picture_list)
                else:
                    if info.xpath('.//img/@src'):
                        preview_picture = info.xpath('.//img/@src')[-1]
                        picture_urls = preview_picture.replace(
                            '/wap180/', '/large/')
                    else:
                        sys.exit(
                            "爬虫微博可能被设置成了'不显示图片'，请前往"
                            "'https://weibo.cn/account/customize/pic'，修改为'显示'"
                        )
            else:
                picture_urls = '无'
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

    def get_one_weibo(self,info):
        """获取一条微博的全部信息"""
        try:
            weibo = OrderedDict()
            is_original = False if len(info.xpath("div/span[@class='cmt']")) > 3 else True
            if (not self.filter) or is_original:
                weibo['id'] = info.xpath('@id')[0][2:]
                weibo['publisher'] = info.xpath('div/a/text()')[0]
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
                if weibo['publish_time'][:10]<self.limit_date:
                    self.flag = False
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
                '发布者',
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
                result_headers.insert(4, '被转发微博原始图片url')
                result_headers.insert(5, '是否为原创微博')
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
            if not self.flag:
                break
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
                    random_pages = random.randint(1, 5)
            except:
                print(res.text)

        if self.got_num > wrote_num:
            self.write_csv(wrote_num)  # 将剩余不足3页的微博写入文件
        if not self.filter:
            print('共爬取' + str(self.got_num) + '条微博')
        else:
            print('共爬取' + str(self.got_num) + '条原创微博')

class WBSSignal(QObject):
    ps = pyqtSignal(str)

# WeiboSearchScrapy 实例和 GUI之间的信号
ss = WBSSignal()

class WBUSignal(QObject):
    ps = pyqtSignal([str,int])

# WeiboUserScrapy 实例和 GUI之间的信号
us = WBUSignal()

# WeiboTopicScrapy 实例和 GUI之间的信号
ts = WBSSignal()

class ScrapyGUI(QMainWindow):

    def __init__(self):
        global ss,vgs,us,ts
        super().__init__()
        self.initUI()

        ss.ps.connect(self.search_user)
        vgs.ps.connect(self.start_user)
        us.ps.connect(self.run_user)

        ts.ps.connect(self.topic_finished)


    def initUI(self):
        self.statusBar().showMessage('准备就绪')
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('关注微信公众号：月小水长')
        self.setWindowIcon(QIcon('logo.jpg'))



        fpAct = QAction(QIcon('fp.png'), '找人(&FP)', self)
        fpAct.setShortcut('Ctrl+P')
        fpAct.setStatusTip('请输入微博用户昵称')
        fpAct.triggered.connect(self.findUser)

        fbAct = QAction(QIcon('fb.png'), '搜微博(&FB)', self)
        fbAct.setShortcut('Ctrl+B')
        fbAct.setStatusTip('请输入微博内容关键词')
        fbAct.triggered.connect(self.findTopic)

        menubar = self.menuBar()
        weiboMenu = menubar.addMenu('微博(&B)')
        weiboMenu.addAction(fpAct)
        weiboMenu.addSeparator()
        weiboMenu.addAction(fbAct)

        settingsMenu = menubar.addMenu('设置(&S)')

        aaAct = QAction(QIcon('aa.png'), '关于作者(&AA)', self)
        aaAct.setShortcut('Ctrl+A')
        aaAct.setStatusTip('产品作者的详细信息')
        aaAct.triggered.connect(self.aboutAuthor)

        aboutMenu = menubar.addMenu('关于(&A)')
        aboutMenu.addAction(aaAct)

        aboutMenu.addSeparator()

        oaAct = QAction(QIcon('oa.png'), '打开官网(&OA)', self)
        oaAct.setShortcut('Ctrl+O')
        oaAct.setStatusTip('打开产品官网')
        oaAct.triggered.connect(self.openAuthority)
        aboutMenu.addAction(oaAct)


        self.pListView = ListView(self)
        self.pListView.setViewMode(QListView.ListMode)
        self.pListView.setStyleSheet("QListView{icon-size:70px}")

        self.pListView.setGeometry(0,20,800,560)

        self.show()

    def findUser(self):
        global filter
        group = QInputDialog.getText(self, "输入用户昵称", "")
        self.searchedUser = group[0]
        if(len(group[0])>0):
            self.pListView.clearData()
            WeiboSearchScrapy(keyword=group[0])

    def findTopic(self):
        dialog = MyDialog(self,info='主题')
        dialog.show()
        if(dialog.exec_()==QDialog.Accepted):
            print(dialog.getData())
            group = dialog.getData()
            topic = group[0]
            filter = 1 if group[1] == True else 0
            WeiboTopicScrapy(keyword=topic,filter=filter,limit_date='2020-01-01')
            QMessageBox.about(self,"提示","已成功将抓取【{}】主题的任务提交后台,结束会通知您".format(topic))

    def aboutAuthor(self):
        QMessageBox.about(self,"作者介绍","简介：985计算机本科在读\nQQ：2391527690\n微信公众号：月小水长")

    def openAuthority(self):
        webbrowser.open("https://inspurer.github.io/")

    def search_user(self,msg):
        print(msg)
        if msg=='EOF':
            QMessageBox.about(self, '提示', '【{}】相关的用户信息加载完毕'.format(self.searchedUser))
            return
        elif msg == 'NetError':
            QMessageBox.warning(self,'警告','请先检查电脑联网情况')
            return
        data = json.loads(msg)
        self.pListView.addItem(data)
        self.show()

    # 监听窗口大小变化事件
    def resizeEvent(self, *args, **kwargs):
        w,h = self.width(),self.height()
        self.pListView.setGeometry(0,20,w,h-40)

    def start_user(self,msg):
        print('wwww',msg)
        res = QMessageBox.question(self,"提示","只抓取原创微博吗？")
        if res==QMessageBox.Yes:
            WeiboUserScrapy(user_id=int(msg),filter=1)
        else:
            WeiboUserScrapy(user_id=int(msg),filter=0)

    def run_user(self,flag,value):
        print(flag,value)
        if flag=='start':
            self.totalPageNum = value
            self.progress = QProgressDialog(self)
            self.progress.setWindowTitle("请稍等")
            self.progress.setLabelText("正在准备抓取...")
            '''
            如果任务的预期持续时间小于minimumDuration，则对话框根本不会出现。这样可以防止弹出对话框，快速完成任务。对于预期超过minimumDuration的任务，对话框将在minimumDuration时间之后或任何进度设置后立即弹出。
            如果设置为0，则只要设置任何进度，将始终显示对话框。 默认值为4000毫秒,即4秒。
            '''
            self.progress.setMinimumDuration(1)
            self.progress.setWindowModality(Qt.WindowModal)
            # 去掉取消按钮
            self.progress.setCancelButtonText(None)
            self.progress.setRange(0, self.totalPageNum)
            self.progress.setValue(1)
        if flag=='run':
            self.progress.setValue(value)
            self.progress.setLabelText("正在抓取第{}/{}页".format(value,self.totalPageNum))

            if value==self.totalPageNum:
                self.progress.destroy()
                QMessageBox.about(self, "提示", "抓取结束")

    def topic_finished(self,msg):
        QMessageBox.about(self,"提示",msg)
        ...
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ScrapyGUI()
    sys.exit(app.exec_())