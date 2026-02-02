# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 22:28:33 2022

@author: user
"""

# app.py

from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print("Data received from Webhook is: ", request.json)
        return "Webhook received!"

app.run(host='0.0.0.0', port=8001)