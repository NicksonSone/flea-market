# -*- coding: utf-8 -*-

import MySQLdb
from functools import wraps
from flask import Flask, jsonify, g, request, make_response
from config import DEBUG
from time import time

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
    userName = request.form["userName"]
    password = request.form["password"]
    phoneNum = request.form["phoneNum"]
    email = request.form["email"]
    QQ = request.form["QQ"]
    location = request.form["location"]
    school = request.form["school"]
    # avatar = request.form["avatar"]
    signUpDate = time()

    # check uniqueness
    cursor = g.db.cursor()
    query = "select userId from User where phoneNum = %s or email = %s"
    cursor.execute(query, (phoneNum, email))
    if cursor.fetchone():
        return jsonify(state=2, error="email or phone number registered")

    # TODO: way to access default avatar unknown
    # stm = ("insert into User"
    #        "(userName, password, phoneNum, email, QQ,"
    #        " location, school, avatar, signUpDate) values "
    #        "(%s, %s, %s, %s, %s,"
    #        " %s, %s, %s, %s)")
    # cursor.execute(stm, (userName, password, phoneNum, email, QQ, location,
    #                      school, avatar, signUpDate))

    stm = ("insert into User"
           "(userName, password, phoneNum, email, QQ,"
           " location, school, signUpDate) values "
           "(%s, %s, %s, %s, %s,"
           " %s, %s, %s)")
    cursor.execute(stm, (userName, password, phoneNum, email, QQ, location,
                         school, signUpDate))

    return jsonify(state=1)


@app.route("/login", methods=['PUT'])
@allow_cross_domain
def login():
    # find user account
    # check password

    account = request.form["account"]
    password = request.form["password"]
    return jsonify(state=1, account=account, password=password)


@app.route("/test", methods=["POST"])
def test():
    num = request.form["num"]
    cursor = g.db.cursor()
    stm = "insert into test values (%s, 1, 'sdf')"
    cursor.execute(stm, (num,))

    return "success"

if __name__ == "__main__":
    app.run()
