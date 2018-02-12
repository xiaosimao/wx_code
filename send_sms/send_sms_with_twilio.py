#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author  : ShiMeng
# @File    : send_sms_with_twilio.py
# @Software: PyCharm

from twilio.rest import Client

# Your Account SID from twilio.com/console
account_sid = "你的sid"
# Your Auth Token from twilio.com/console
auth_token  = "你的token"

client = Client(account_sid, auth_token)

message = client.messages.create(
    to="+86验证过的号码",
    from_="+twilio给你的号码 ",
    body="你好!")

print(message.sid)

