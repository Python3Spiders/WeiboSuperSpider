# -*- coding: utf-8 -*-
# 作者:             inspurer(月小水长)
# 创建时间:          2020/11/1 19:43
# 运行环境           Python3.6+
# github            https://github.com/inspurer
# qq邮箱            2391527690@qq.com
# 微信公众号         月小水长(ID: inspurer)
# 文件备注信息       todo


import csv
import os
import random
import re
import sys
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from time import sleep
import pandas as pd

import requests

requests.packages.urllib3.disable_warnings()
from lxml import etree
import json

User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0'
Cookie = '换成你自己的 cookie, 可以参考：https://www.bilibili.com/video/BV1934y127ZM  感谢 @Simon_阿文 写的入门级食用教程：https://weibo.com/1757693565/Mswzx0UEy'


class WeiboUserScrapy():
    IMG_LINK_SEP = ' '
    IMG_SAVE_ROOT = 'img'

    def __init__(self, user_id, filter=0, download_img=False):
        global headers
        self.headers = {
            'Cookie': Cookie,
            'User_Agent': User_Agent
        }

        if filter != 0 and filter != 1:
            sys.exit('filter值应为0或1,请重新输入')

        self.user_id = str(user_id)  # 用户id,即需要我们输入的数字,如昵称为"Dear-迪丽热巴"的id为1669879400
        self.filter = filter  # 取值范围为0、1,程序默认值为0,代表要爬取用户的全部微博,1代表只爬取用户的原创微博
        self.download_img = download_img  # 微博抓取結束后是否下载微博图片
        self.nickname = ''  # 用户昵称,如“Dear-迪丽热巴”
        self.weibo_num = 0  # 用户全部微博数
        self.got_num = 0  # 爬取到的微博数
        self.following = 0  # 用户关注数
        self.followers = 0  # 用户粉丝数
        self.weibo = []  # 存储爬取到的所有微博信息
        if not os.path.exists('user'):
            os.mkdir('user')
        if not os.path.exists(self.IMG_SAVE_ROOT):
            os.mkdir(self.IMG_SAVE_ROOT)
        if self.download_img:
            self.img_save_folder = os.path.join(self.IMG_SAVE_ROOT, self.user_id)
            if not os.path.exists(self.img_save_folder):
                os.mkdir(self.img_save_folder)
        self.run()

    def deal_html(self, url):
        """处理html"""
        try:
            html = requests.get(url, headers=self.headers, verify=False).content
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

            self.weibo_num = (user_info[0][3:-1])
            print('微博数: ' + str(self.weibo_num))

            self.following = (user_info[1][3:-1])
            print('关注数: ' + str(self.following))

            self.followers = (user_info[2][3:-1])
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
                sleep(2)
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
        print('开始提取图片 URL')
        """提取微博原始图片url"""
        try:
            selector = self.deal_html(f"https://weibo.cn/mblog/picAll/{weibo_id}?rl=2")
            if not selector:
                return ''
            sleep(1)
            picture_list = selector.xpath('//img/@src')
            picture_list = [
                p.replace('/thumb180/', '/large/').replace('/wap180/', '/large/')
                for p in picture_list
            ]
            print(picture_list)
            picture_urls = self.IMG_LINK_SEP.join(picture_list)
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
                weibo['link'] = 'https://weibo.cn/comment/{}?uid={}&rl=0#cmtfrm'.format(weibo['id'], self.user_id)
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
            url = f'https://weibo.cn/{self.user_id}/profile?page={page}'
            selector = self.deal_html(url)
            info = selector.xpath("//div[@class='c']")
            is_exist = info[0].xpath("div/span[@class='ctt']")
            if is_exist:
                for i in range(0, len(info) - 1):
                    weibo = self.get_one_weibo(info[i])
                    if weibo:
                        self.weibo.append(weibo)
                        self.got_num += 1
                        print('-' * 100)
        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    @staticmethod
    def drop_duplicate(file_path):
        df = pd.read_csv(file_path)
        # print(df.shape[0])
        df.drop_duplicates(keep='first', subset=['wid'], inplace=True)
        # 去重重复 header
        df.drop(df[df['publish_time'].isin(['publish_time'])].index, inplace=True)
        # print(df.shape[0])
        df.sort_values(by=['publish_time'], ascending=False, inplace=True)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')

    def write_csv(self, wrote_num):
        """将爬取的信息写入csv文件"""
        try:
            result_headers = [
                'wid',
                'weibo_link',
                'content',
                'img_urls',
                'location',
                'publish_time',
                'publish_tool',
                'like_num',
                'forward_num',
                'comment_num',
            ]
            if not self.filter:
                result_headers.insert(4, 'origin_img_urls')
                result_headers.insert(5, 'is_origin')
            result_data = [w.values() for w in self.weibo][wrote_num:]
            self.file_path = './user/{}_{}.csv'.format(self.user_id, self.nickname)
            # with open('./user/{}_{}_{}博_{}粉_{}关注.csv'.format_excc(self.user_id,self.nickname,self.weibo_num, self.followers,self.following),'a',encoding='utf-8-sig',newline='') as f:
            with open(self.file_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                if wrote_num == 0:
                    writer.writerows([result_headers])
                writer.writerows(result_data)
            self.drop_duplicate(self.file_path)
            print(u'%d条微博写入csv文件完毕:' % self.got_num)

        except Exception as e:
            print('Error: ', e)
            traceback.print_exc()

    def write_file(self, wrote_num):
        """写文件"""
        if self.got_num > wrote_num:
            self.write_csv(wrote_num)

    def get_weibo_info(self):
        """获取微博信息"""
        try:
            url = f'https://weibo.cn/{self.user_id}/profile'
            selector = self.deal_html(url)
            self.get_user_info(selector)  # 获取用户昵称、微博数、关注数、粉丝数
            page_num = self.get_page_num(selector)  # 获取微博总页数
            wrote_num = 0
            page1 = 0
            user_page_config = 'user_page.json'
            if not os.path.exists('user_page.json'):
                page = 1
                with open(user_page_config, 'w', encoding='utf-8-sig') as f:
                    f.write(json.dumps({f'{self.user_id}': page}, indent=2))
            else:
                with open(user_page_config, 'r', encoding='utf-8-sig') as f:
                    raw_json = json.loads(f.read())
                    if self.user_id in raw_json.keys():
                        page = raw_json[self.user_id]
                    else:
                        page = 0

            random_pages = random.randint(1, 5)
            for page in range(page, page_num + 1):
                self.get_one_page(page)  # 获取第page页的全部微博

                with open(user_page_config, 'r', encoding='utf-8-sig') as f:
                    old_data = json.loads(f.read())
                    old_data[f'{self.user_id}'] = page

                with open(user_page_config, 'w', encoding='utf-8-sig') as f:
                    f.write(json.dumps(old_data, indent=2))

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

    def do_down_img(self, img_url, savepath):
        if os.path.exists(savepath):
            print(f'{img_url} 已经下载过')
            return
        try:
            print(f"正在下载图片 {img_url} ...")
            with open(savepath, 'wb') as fp:
                response = requests.get(url=img_url, headers=self.headers)
                fp.write(response.content)
            print('图片下载成功')
            sleep(1)
        except:
            print('图片下载失败')

    def get_weibo_img(self):
        '''下载相册图片'''
        if self.download_img:
            df = pd.read_csv(self.file_path)
            for index, row in df.iterrows():
                print(f'index: {index + 1} / {df.shape[0]}')
                # 下载相册图片使用 img_urls
                # 下载转发过的微博里面的图片使用 origin_img_urls

                image_cols = ['img_urls']
                if not self.filter:
                    image_cols.append('origin_img_urls')

                wid = row['wid']

                for ic in image_cols:
                    image_urls = row[ic]
                    if image_urls == None or isinstance(image_urls, float) or image_urls == '' or image_urls == '无':
                        pass
                    else:
                        image_urls = image_urls.split(self.IMG_LINK_SEP)
                        for index, image_url in enumerate(image_urls):
                            self.do_down_img(image_url, os.path.join(self.img_save_folder, f'{wid}_{ic[:-5]}_{index + 1}.jpg'))

    def run(self):
        """运行爬虫 """
        try:
            print('开始抓取微博')
            self.get_weibo_info()
            print('微博抓取完毕，开始下载相册图片')
            self.get_weibo_img()
            print('*' * 100)

        except Exception as e:
            print('Error: ', e)
            print(traceback.format_exc())


if __name__ == '__main__':
    # 注意关闭 vpn，注意配置代码第 29 行处的 cookie
    # 2023.2.12 更新
    # 1、解决无法抓取 cookie 对应账号微博的问题
    # 2、解决微博抓取不全的问题，解决微博全文无法获取的问题（有待多次验证）
    # 3、可选下载所有图片（包括微博相册和转发微博里面的图片），参数为 download_img，默认为 False 不下载
    WeiboUserScrapy(user_id=6859133019, filter=0, download_img=True)
