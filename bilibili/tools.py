# coding:utf-8
from config import download_delay

import requests
import time
import hashlib
import urlparse
from config import base_header


def request(url, header):

    try:
        con = requests.get(url, headers=header)
    except Exception, e:
        print 'ERROR IN [{url}]'.format(url=url)
        print 'ERROR INFO [{E}]'.format(E=e)
        return None
    else:

        if  con.status_code == 404:
            print url
            print header

        if con.status_code == 200 :
            return con
        else:
            raise ValueError('{url} code is {code}'.format(url=url, code=con.status_code))
    finally:
        time.sleep(download_delay)


def download(pwd, true_url, page_url):
    print 'DOWNLOADING'
    host = urlparse.urlparse(true_url).netloc
    save_headers = {
        'host': host,
        'referer': page_url,
        'user-agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36"
    }

    video_content = request(true_url, header=save_headers)
    print 'video status:', video_content.status_code

    with open(pwd, 'wb') as f:
        f.write(video_content.content)


def get_sign(params, appkey, appsecret):
    params['appkey'] = appkey
    data = ""
    paras = sorted(params)
    paras.sort()
    for para in paras:
        if data != "":
            data += "&"
        data += para + "=" + str(params[para])
    if appsecret == None:
        return data
    m = hashlib.md5()
    m.update((data + appsecret).encode('utf-8'))
    return data + '&sign=' + m.hexdigest()
