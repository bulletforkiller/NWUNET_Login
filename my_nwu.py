#!/usr/bin/python3
# -*- coding:utf-8 -*-

import json
import getpass
import requests
from bs4 import BeautifulSoup
import urllib.parse as urlparse


def get_user_pass():
    username = input('请输入帐号：')
    password = getpass.getpass(prompt="请输入密码：")
    return username, password


class MyNWUNET(object):
    url_login = '/portal/api/v2/online'
    url_session = '/portal/api/v2/session/list'
    url_logout = '/portal/api/v2/session/acctUniqueId/'
    ua = {
        'PC':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3730.0 Safari/537.36',
        'Android':
        'Mozilla/5.0 (Linux; Android 8.1.0; INE-LX2 Build/HUAWEIINE-LX2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.91 Mobile Safari/537.36'
    }

    def __init__(self, device_type, raw_url=None):
        self.device_type = device_type
        self.raw_url = raw_url if raw_url else 'http://www.baiadu.com'

    def get_web_info(self):
        res = requests.get(self.raw_url)
        self.probe_data = res.text

    def _need_authenticated(self):
        feature_str = 'Authentication is required.'
        if feature_str in self.probe_data:
            self.is_login = False
        else:
            self.is_login = True

    def get_login_info(self):
        self.get_web_info()
        soup = BeautifulSoup(self.probe_data, 'html.parser')
        self.referer = soup.find('a')['href']
        self.host = urlparse.urlsplit(self.referer).netloc
        self.url_base = self.referer.split('?')[0]
        params = urlparse.parse_qs(urlparse.urlsplit(self.referer).query)
        params = {k: v[0] for k, v in params.items()}
        self._device_info = params

    def get_user_info(self, func):
        self.username, self.password = func()

    def get_session(self):
        res = requests.get(
            self.url_base + self.url_session, headers=self.header)
        self.session = json.loads(res.text)['sessions'][0]['acct_unique_id']

    def login(self):
        self.get_login_info()
        self.get_user_info(get_user_pass)
        if not self._need_authenticated():
            return False
        self.header = {
            'Host': self.host,
            'User-Agent': self.ua[self.device_type],
            'Content-type': 'application/json',
        }
        post_data = {
            'deviceType': self.device_type,
            'webAuthUser': self.username,
            'webAuthPassword': self.password,
            'redirectUrl': self.referer,
            'type': 'login',
        }
        res = requests.post(
            self.url_base + self.url_login,
            data=json.dumps(post_data),
            headers=self.header)
        if res.status_code == 200:
            self.header['Authorization'] = json.loads(res.text)["token"]
            self.get_session()
            return True
        else:
            return False

    def logout(self):
        if not hasattr(self, 'session'):
            return False
        else:
            url = self.url_base + self.url_logout + self.session
            res = requests.delete(url, headers=self.header)
            if res.status_code == 200:
                return True
            else:
                return False


if __name__ == "__main__":
    # Test
    a = MyNWUNET('PC')
    a.login()
