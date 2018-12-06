#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 18-12-5 上午10:54
# @Author  : ShiMeng
# @File    : dzdp.py
# @Software: PyCharm

import requests
import re
from lxml import etree
import lxml.html as H
import math

"""
大众点评CSS破解
没有做太多的优化，因为没有大量的代理，爬不了太多的内容
这里只是跟大家分享一下处理的流程。
具体见：https://cuiqingcai.com/?p=6341
我的个人二维码在上面的文章中，欢迎拍砖交流
"""

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
}
r = requests.get("http://www.dianping.com", headers=headers)
_cookie = ''
for cookie in  r.cookies:
    _cookie += "%s=%s;"%(cookie.name, cookie.value)

headers.update({"Cookie": _cookie})


def get_tag(_list, offset=1):
    _new_list = [data[0:offset] for data in _list]

    if len(set(_new_list)) == 1:
        # 说明全部重复
        offset += 1
        return get_tag(_list, offset)
    else:
        _return_data = [data[0:offset - 1] for data in _list][0]

        return _return_data


def get_css(content):
    matched = re.search(r'href="([^"]+svgtextcss[^"]+)"', content, re.M)
    if not matched:
        raise Exception("cannot find svgtextcss file")
    css_url = matched.group(1)

    css_url = "https:" + css_url
    class_tag = re.findall("<b><span class=\"(.*?)\"></span>", content)
    _tag = get_tag(class_tag)

    return css_url, _tag


def get_svg_threshold_and_int_dict(css_url, _tag):
    con = requests.get(css_url, headers=headers).content.decode("utf-8")
    index_and_word_dict = {}
    # 根据tag值匹配到相应的svg的网址

    find_svg_url = re.search(r'span\[class\^="%s"\].*?background\-image: url\((.*?)\);' % _tag, con)
    if not find_svg_url:
        raise Exception("cannot find svg file, check")
    svg_url = find_svg_url.group(1)
    svg_url = "https:" + svg_url
    svg_content = requests.get(svg_url, headers=headers).content
    svg_doc = H.document_fromstring(svg_content)
    datas = svg_doc.xpath("//text")
    # 把阈值和对应的数字集合放入一个字典中
    last = 0
    for index, data in enumerate(datas):
        y = int(data.xpath('@y')[0])
        int_set = data.xpath('text()')[0]
        index_and_word_dict[int_set] = range(last, y+1)
        last = y
    return index_and_word_dict


def get_css_and_px_dict(css_url):
    con = requests.get(css_url, headers=headers).content.decode("utf-8")
    find_datas = re.findall(r'(\.[a-zA-Z0-9-]+)\{background:(\-\d+\.\d+)px (\-\d+\.\d+)px', con)
    css_name_and_px = {}
    for data in find_datas:
        # 属性对应的值
        span_class_attr_name = data[0][1:]
        # 偏移量
        offset = data[1]
        # 阈值
        position = data[2]
        css_name_and_px[span_class_attr_name] = [offset, position]
    return css_name_and_px


def get_data(url ):
    """
    :param page_url: 待获取url
    :return:
    """
    con = requests.get(url, headers=headers).content.decode("utf-8")
    # 获取css url，及tag
    css_url, _tag = get_css(con)
    # 获取css对应名与像素的映射
    css_and_px_dict = get_css_and_px_dict(css_url)
    # 获取svg的阈值与数字集合的映射
    svg_threshold_and_int_dict = get_svg_threshold_and_int_dict(css_url, _tag)

    doc = etree.HTML(con)
    shops = doc.xpath('//div[@id="shop-all-list"]/ul/li')
    for shop in shops:
        # 店名
        name = shop.xpath('.//div[@class="tit"]/a')[0].attrib["title"]

        comment_num = 0
        price_num = taste = service= environment = 0
        comment_and_price_datas = shop.xpath('.//div[@class="comment"]')
        for comment_and_price_data in comment_and_price_datas:
            _comment_data = comment_and_price_data.xpath('a[@class="review-num"]/b/node()')
            # 遍历每一个node，这里node的类型不同，分别有etree._ElementStringResult(字符)，etree._Element（元素），etree._ElementUnicodeResult（字符）
            for _node in _comment_data:
                # 如果是字符，则直接取出
                if isinstance(_node, etree._ElementStringResult):
                    comment_num = comment_num * 10 + int(_node)
                else:
                    # 如果是span类型，则要去找数据
                    # span class的attr
                    span_class_attr_name = _node.attrib["class"]
                    # 偏移量，以及所处的段
                    offset, position = css_and_px_dict[span_class_attr_name]
                    index = abs(int(float(offset) ))
                    position = abs(int(float(position)))
                    # 判断
                    for key, value in svg_threshold_and_int_dict.iteritems():
                        if position in value:
                            threshold = int(math.ceil(index/12))
                            number = int(key[threshold])
                            comment_num = comment_num * 10 + number

            _price = comment_and_price_data.xpath('a[@class="mean-price"]/b/node()')
            for price_node in _price:
                if isinstance(price_node, etree._ElementUnicodeResult):
                    if len(price_node) > 1:
                        price_num = price_num * 10 + int(price_node[1:])
                elif isinstance(price_node, etree._ElementStringResult):
                    price_num = price_num * 10 + int(price_node)
                else:
                    span_class_attr_name = price_node.attrib["class"]
                    # 偏移量，以及所处的段
                    offset, position = css_and_px_dict[span_class_attr_name]
                    index = abs(int(float(offset)))
                    position = abs(int(float(position)))
                    # 判断
                    for key, value in svg_threshold_and_int_dict.iteritems():
                        if position in value:
                            threshold = int(math.ceil(index / 12))
                            number = int(key[threshold])
                            price_num = price_num * 10 + number

        others_num_node = shop.xpath('.//span[@class="comment-list"]/span')
        for others_datas in others_num_node:
            if others_datas.xpath('text()') and others_datas.xpath('text()')[0] == u"口味":
                _taste_data = others_datas.xpath('b/node()')
                for _taste in _taste_data:
                    if isinstance(_taste, etree._Element):
                        css_class = _taste.attrib["class"]
                        # 偏移量，以及所处的段
                        offset, position = css_and_px_dict[css_class]
                        index = abs(int(float(offset)))
                        position = abs(int(float(position)))
                        # 判断
                        for key, value in svg_threshold_and_int_dict.iteritems():
                            if position in value:
                                threshold = int(math.ceil(index / 12))
                                number = int(key[threshold])
                                taste = taste * 10 + number
                    else:
                        if len(_taste) > 1:  #
                            taste = taste * 10 + int(_taste[1:])

            if others_datas.xpath('text()') and others_datas.xpath('text()')[0] == u"服务":
                _taste_data = others_datas.xpath('b/node()')
                for _taste in _taste_data:
                    if isinstance(_taste, etree._Element):
                        css_class = _taste.attrib["class"]
                        # 偏移量，以及所处的段
                        offset, position = css_and_px_dict[css_class]
                        index = abs(int(float(offset)))
                        position = abs(int(float(position)))
                        # 判断
                        for key, value in svg_threshold_and_int_dict.iteritems():
                            if position in value:
                                threshold = int(math.ceil(index / 12))
                                number = int(key[threshold])
                                service = service * 10 + number
                    else:
                        if len(_taste) > 1:  #
                            service = service * 10 + int(_taste[1:])

            if others_datas.xpath('text()') and others_datas.xpath('text()')[0] == u"环境":
                _taste_data = others_datas.xpath('b/node()')
                for _taste in _taste_data:
                    if isinstance(_taste, etree._Element):
                        css_class = _taste.attrib["class"]
                        offset, position = css_and_px_dict[css_class]
                        index = abs(int(float(offset)))
                        position = abs(int(float(position)))
                        # 判断
                        for key, value in svg_threshold_and_int_dict.iteritems():
                            if position in value:
                                threshold = int(math.ceil(index / 12))
                                number = int(key[threshold])
                                environment = environment * 10 + number
                    else:
                        if len(_taste) > 1:
                            environment = environment * 10 + int(_taste[1:])
        print("restaurant: {}\n, "
              "comment total num: {}\n, "
              "price num: {}\n,"
              "taste score:{}\n,"
              "service socre:{}\n, "
              "environment_score:{}, "
              "\n ".
              format(name.encode('utf-8'), comment_num, price_num, taste, service, environment))


if __name__ == '__main__':
    url = "https://www.dianping.com/suzhou/ch10/g110"
    get_data(url)
