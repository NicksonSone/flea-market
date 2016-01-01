# -*- coding: utf-8 -*-

import MySQLdb
import base64
from functools import wraps
from flask import Flask, jsonify, g, request, make_response
from config import DEBUG

app = Flask(__name__)
app.debug = DEBUG
app.config.from_pyfile("config.py")

from sae.const import (MYSQL_HOST,
                       MYSQL_PORT, MYSQL_USER, MYSQL_PASS, MYSQL_DB
                       )


@app.before_request
def before_request():
    g.db = MySQLdb.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS,
                           MYSQL_DB, port=int(MYSQL_PORT))


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def allow_cross_domain(fun):
    @wraps(fun)
    def wrapper_fun(*args, **kwargs):
        rst = make_response(fun(*args, **kwargs))
        rst.headers['Access-Control-Allow-Origin'] = '*'
        rst.headers['Access-Control-Allow-Methods'] = (
            'PUT,GET,POST,DELETE,OPTIONS')
        allow_headers = "Referer,Accept,Origin,User-Agent, Content-Type"
        rst.headers['Access-Control-Allow-Headers'] = allow_headers
        return rst
    return wrapper_fun


@app.route("/", methods=['GET'])
def frontPage():
    return "front page"


@app.route("/register", methods=['POST', 'OPTIONS'])
@allow_cross_domain
def register():
    # check mailbox, phone number
    # insert data into database
    username = request.form["username"]
    return username
    base64.b64encode(username)
    # password = request.form["password"]
    # phoneNum = request.form["phoneNum"]
    # mailbox = request.form["mailbox"]
    # QQ = request.form["QQ"]
    # location = request.form["location"]
    # school = request.form["school"]

    # cursor = g.db.cursor()
    # cursor.execute("select * from test")
    # results = cursor.fetchall()
    # cursor = g.db.cursor()
    # cursor.execute(
    #     "insert into test values(1, 2, %s)",
    #     (username,)
    # )

    # cursor.execute("select * from test")
    # results = cursor.fetchall()

    # return jsonify(results=results)


@app.route("/login", methods=['PUT'])
@allow_cross_domain
def login():
    # find user account
    # check password

    account = request.form["account"]
    password = request.form["password"]
    return jsonify(stat=1, account=account, password=password)


if __name__ == "__main__":
    app.run()
