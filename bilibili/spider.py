#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 18-5-12 下午2:32
# @Author  : ShiMeng
# @File    : spider.py
# @Software: PyCharm

import time
import re
import os

from threading import Thread
from Queue import Queue
from tools import request
from tools import get_sign, download
from config import base_header
from config import space_ids
from config import appkey, appsecret
from config import download_thread_num, download_status, show_size_status


video_url_queue = Queue()


class Bilibili(object):


    # 获取所有的aid
    def get_video_aid(self, space_id):
        pages_num_url = "http://space.bilibili.com/ajax/member/getSubmitVideos?mid={space_id}&pagesize=30&tid=0&page=1&keyword=&order=senddate".format(
            space_id=space_id)

        con = request(pages_num_url, header=base_header)
        if con:
            try:
                pages_num = int(con.json()["data"]["pages"])
            except Exception, e:
                print 'IN get_video_aid '
                print e
            else:
                for i in range(1, pages_num):
                    url = "http://space.bilibili.com/ajax/member/getSubmitVideos?mid={space_id}&pagesize=30&tid=0&page=1&keyword=&order=senddate".format(
                        space_id=space_id)

                    html_json = request(url, header=base_header)
                    video_json_list = html_json.json()

                    for data in video_json_list.get('data').get('vlist'):
                        yield data.get('aid')

    # 获取aid的分P页数
    def get_each_aid_page_num(self, space_id):
        for aid in self.get_video_aid(space_id):
            url = 'https://www.bilibili.com/video/av{aid}'.format(aid=aid)
            con = request(url, header=base_header)
            if con:
                page_num_pattern = '{aid},\"videos\":(\d+)'.format(aid=aid)
                page = re.findall(page_num_pattern, con.content)
                if page:
                    page = int(page[0])
                    yield page, aid

    # 获取一级标题和二级标题，创建文件夹
    def get_title_and_each_page_cid(self, space_ids):
        for space_id in space_ids:
            for i, aid in self.get_each_aid_page_num(space_id):
                page_num = i + 1
                for j in range(1, page_num):

                    url = 'http://api.bilibili.com/view?type=jsonp&appkey=8e9fc618fbd41e28&id={aid}&page={page}'.format(
                        aid=aid, page=j)
                    con = request(url, header=base_header)
                    if con:
                        content = con.json()

                        title = content.get('title').replace('/', '_')
                        partname = content.get('list').get('0').get('part')
                        cid = content.get('list').get('0').get('cid')
                        # 创建文件夹
                        if not os.path.exists(title):
                            os.mkdir(title)
                        # get download_url

                        page_url = 'https://www.bilibili.com/video/av{aid}/?p={page}'.format(aid=aid, page=j)
                        download_api_url = self.get_video_download_api_url(cid)

                        download_content = request(download_api_url, header=None).json()
                        durl = download_content.get('durl')
                        if durl:
                            for data in durl:
                                order = data.get('order')
                                true_video_url = data.get('url')
                                save_name = str(j) + '_' + partname + '_' + str(order) + '.flv'

                                pwd = os.path.join(os.path.join(os.getcwd(), title), save_name)
                                video_url_queue.put((pwd, true_video_url, page_url))

    def get_video_download_api_url(self, cid, appkey=None, appscret=None):
        base_url = 'http://interface.bilibili.com/playurl?'
        params = {'otype': 'json', 'cid': cid, 'type': 'flv', 'quality': 1, 'appkey': appkey, 'from': 'local',
                  'player': 1
                  }
        sign_data = get_sign(params, appkey=appkey, appsecret=appsecret)
        return base_url + sign_data

    def _go(self):
        while 1:
            if not video_url_queue.empty():
                pwd, true_url, page_url = video_url_queue.get()
                download(pwd, true_url, page_url)
                video_url_queue.task_done()

    def _show_size(self):
        def show_size():
            while 1:
                if not video_url_queue.empty():
                    print video_url_queue.qsize()
                    time.sleep(3)


    def run(self):
        # 获取下载url的线程
        t1 = Thread(target=self.get_title_and_each_page_cid, args=(space_ids,))
        t1.start()
        # 下载视频的线程
        if download_status:
            t2_list = []
            for i in range(download_thread_num):
                t2 = Thread(target=self._go)
                t2_list.append(t2)

            for _t2 in t2_list:
                _t2.start()

            for __t2 in t2_list:
                __t2.join()
        # 显示size的线程
        if show_size_status:
            t3 = Thread(target=self._show_size)

            t3.start()

            t1.join()

            t3.join()

if __name__ == '__main__':
    bilibili = Bilibili()
    bilibili.run()

