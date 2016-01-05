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


def parseData():
    data = list(request.form.iterkeys())[0]
    data = ast.literal_eval(data)
    return data


@app.route("/", methods=['GET'])
def frontPage():
    return "front page"


@app.route("/register", methods=['POST', 'OPTIONS'])
@allow_cross_domain
def register():
    # check mailbox, phone number
    # insert data into database
    data = parseData()

    userName = data.get("userName", "")
    password = data.get("password", "")
    phoneNum = data.get("phoneNum", "")
    email = data.get("email", "")
    QQ = data.get("QQ", "")
    location = data.get("location", "")
    school = data.get("school", "")
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
    g.db.commit()

    # get userId to check the insertion
    query = "select userId, password from User where email = %s"
    cursor.execute(query, (email,))
    record = cursor.fetchone()
    userId = record[0]

    if userId is None:
        return jsonify(state=0, error="unable to register for unknbwn reasons")

    return jsonify(state=1, userId=userId)


@app.route("/login", methods=["POST", "OPTIONS"])
@allow_cross_domain
def login():
    # find user account
    # check password

    data = parseData()
    account = data.get("account", "")
    password = data.get("password", "")

    query = "select userId, password from User where email = %s"
    cursor = g.db.cursor()
    cursor.execute(query, (account,))
    record = cursor.fetchone()

    if record is None:
        return jsonify(state=3, error="user does not exist")

    if password != record[1]:
        return jsonify(state=2, error="incorrect password")

    return jsonify(state=1, userId=record[0])


@app.route("/user/password", methods=["POST", "OPTIONS"])
@allow_cross_domain
def change_pwd():
    # data = parseData()
    email = request.form.get("email", "")
    oldPwd = request.form.get("oldpassword", "")
    newPwd = request.form.get("npassword", "")

    cursor = g.db.cursor()
    query = "select userId from User where email = %s and password = %s"
    cursor.execute(query, (email, oldPwd))
    record = cursor.fetchone()

    if not record:
        return jsonify(state=0)

    update = "update User set password = %s where email = %s "
    cursor.execute(update, (newPwd, email))
    g.db.commit()

    return jsonify(state=1)


@app.route("/user", methods=["GET", "OPTIONS"])
@allow_cross_domain
def get_user_info():
    # retrieve user info by userId

    userId = request.args.get("userId", None)
    if not userId:
        return jsonify(state=0, error="no arguement passed")

    userId = int(userId)
    query = ("select userName, realName, phoneNum, QQ, location, school from User where userId = %s")
    cursor = g.db.cursor()
    cursor.execute(query, (userId,))
    result = cursor.fetchone()

    return jsonify(state=1, result=result)


@app.route("/user", methods=["POST", "OPTIONS"])
def edit_user_info():
    data = parseData()
    userId = data.get("userId", None)
    userName = data.get("userName", None)
    realName = data.get("realName", None)
    QQ = data.get("QQ", None)
    location = data.get("location", None)
    school = data.get("school", None)

    cursor = g.db.cursor()
    update = ("update User set userName = %s, realName = %s, "
              "QQ = %s, location = %s, school = %s"
              "where userId = %s")
    cursor.execute(update, (userName, realName, QQ, location, school, userId))
    g.db.commit()

    return jsonify(state=1)


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
