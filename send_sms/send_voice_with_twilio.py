#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 18-2-11 上午9:01
# @Author  : ShiMeng
# @File    : send_voice_with_twilio.py
# @Software: PyCharm


# Download the Python helper library from twilio.com/docs/python/install
from twilio.rest import Client

# Your Account Sid and Auth Token from twilio.com/user/account
account_sid = "your sid"
auth_token = "your token"
client = Client(account_sid, auth_token)

call = client.calls.create(
    to="+86验证过的号码",
    from_="+twilio给你的号码 ",
    url="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient",
    method="GET",
    status_callback="https://www.myapp.com/events",
    status_callback_method="POST",
    status_callback_event=["initiated", "ringing", "answered", "completed"]
)

print(call.sid)
