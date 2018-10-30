#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json

from flask import Flask, render_template
import pymongo

import scrape_mars


# Create Flask application
app = Flask(__name__)

# Create client for MongoDB
mongo_client = pymongo.MongoClient('mongodb://localhost:27017/mission_to_mars')

# / render index.html
@app.route('/')
def index():
    data = mongo_client.db.mission_to_mars.find_one(sort=[('create_time', pymongo.DESCENDING)])
    return render_template('index.html', data=data)


# /scrape scrape all data and save to MongoDB
@app.route('/scrape')
def scrape():
    status = -1
    try:
        mission_to_mars = mongo_client.db.mission_to_mars
        data, msg = scrape_mars.scrape()
        if data is not None:
            mission_to_mars.insert(data)
            status = 0
    except Exception as e:
        status, msg = -1, str(e)
    return json.dumps({'status': status, 'msg': msg, 'data': data})


if __name__ == '__main__':
    app.run()
