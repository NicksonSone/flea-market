# -*- coding: utf-8 -*-

import ast
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
    # userName = request.values.get("userName", "")
    # return jsonify(state=request.values)
    s = request.data
    data = "'" + s[1:] + "'"
    r = ast.literal_eval(data)
    return jsonify(state=r)
    password = request.form.get("password", "")
    phoneNum = request.form.get("phoneNum", "")
    email = request.form.get("email", "")
    QQ = request.form.get("QQ", "")
    location = request.form.get("location", "")
    school = request.form.get("school", "")
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

    # insert user data
    stm = ("insert into User"
           "(userName, password, phoneNum, email, QQ,"
           " location, school, signUpDate ) values "
           "(%s, %s, %s, %s, %s,"
           " %s, %s, %s)")
    cursor.execute(stm, (userName, password, phoneNum, email, QQ, location,
                         school, signUpDate))

    # get userId to check the insertion
    query = "select userId from User where email = %s"
    cursor.execute(query, (email,))
    # TODO: fetch userId
    userId = cursor.fetchone()

    if userId is None:
        return jsonify(state=0, error="unable to register for unknbwn reasons")

    return jsonify(state=1, userId=userId)


@app.route("/login", methods=["PUT"])
@allow_cross_domain
def login():
    # find user account
    # check password

    account = request.form.get("account", "")
    password = request.form("password", "")

    query = "select userId, password from User where email = %s"
    cursor = g.db.cursor()
    cursor.execute(query, (account,))
    # TODO: fetch userId and password
    result = cursor.fetchone()

    if result is None:
        return jsonify(state=3, error="user does not exist")

    if password != result:
        return jsonify(state=2, error="incorrect password")

    return jsonify(state=1, account=account, password=password)


@app.route("/user", methods=["GET"])
@allow_cross_domain
def get_user_info():
    # retrieve user info by userId

    userId = request.args.get("userId", None)
    if not userId:
        return jsonify(state=0, error="no arguement passed")

    query = ("select userName, phoneNum, QQ, email, location, school, avatar"
             "from userId where userId = %s")
    cursor = g.db.cursor()
    cursor.execute(query, (userId,))
    result = cursor.fetchone()

    return jsonify(state=1, result=result)


@app.route("/test", methods=["POST"])
def test():
    num = request.form["num"]
    cursor = g.db.cursor()
    cursor.execute("select signUpDate from User where userId = %s", (num,))
    c = cursor.fetchone()
    c = str(c)
    return jsonify(result=c)

if __name__ == "__main__":
    app.run()
