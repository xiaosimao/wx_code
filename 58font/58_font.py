# coding=utf-8
import requests
import re
import time
import  lxml.html as H
import base64
from fontTools.ttLib import TTFont


def get_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    }
    session = requests.session()
    con = session.get(url, headers=headers)
    doc = H.document_fromstring(con.content)

    font_data_origin = re.search(r'base64,(.*?)\)', con.content, re.S).group(1)
    font_data_after_decode = base64.b64decode(font_data_origin)

    new_font_name = "font_new.ttf"
    with open(new_font_name, 'wb') as f:
        f.write(font_data_after_decode)

    map_data = tff_parse(new_font_name)
    names = doc.xpath('//span[@class="infocardName fl stonefont resumeName"]/text()')
    # 有的时候会找不到，可以多执行几次；
    if names:
        for name in names:
            print 'name in page source', name
            for j in map_data.keys():
                    name = name.replace(j, map_data[j])
            print 'name actual', name

def tff_parse(font_parse_name):
    # 我这里的字体的顺序，如果你的不同，一定要修改
    font_dict = [u'博', u'经', u'硕', u'届', u'大', u'刘', u'8', u'1', u'士', u'E', u'2', u'6', u'张',
                 u'M', u'验', u'5', u'本', u'赵', u'陈', u'吴', u'李', u'生', u'4', u'校', u'以', u'应', u'黄',
                 u'技', u'无', u'女', u'A', u'周', u'中', u'3', u'王', u'7', u'0', u'9', u'科', u'高', u'男',
                 u'杨', u'专', u'下', u'B']
    font_base = TTFont('font_base.ttf')
    font_base_order = font_base.getGlyphOrder()[1:]
    # font_base.saveXML('font_base.xml')  调试用

    font_parse = TTFont(font_parse_name)
    # font_parse.saveXML('font_parse_2.xml')调试用
    font_parse_order = font_parse.getGlyphOrder()[1:]

    f_base_flag = []
    for i in font_base_order:
        flags = font_base['glyf'][i].flags
        f_base_flag.append(list(flags))

    f_flag = []
    for i in font_parse_order:
        flags = font_parse['glyf'][i].flags
        f_flag.append(list(flags))

    result_dict = {}
    for a, i in enumerate(f_base_flag):
        for b, j in enumerate(f_flag):
            if comp(i, j):
                key = font_parse_order[b].replace('uni', '')
                key = eval(r'u"\u' + str(key) + '"').lower()
                result_dict[key] = font_dict[a]
    return result_dict

def comp(L1, L2):

    if len(L1) != len(L2):
        return 0
    for i in xrange(len(L2)):
        if L1[i] == L2[i]:
            pass
        else:
            return 0
    return 1




if __name__ == '__main__':
    url = "https://su.58.com/qztech/"
    get_data(url)


