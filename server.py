# -*- coding: utf-8 -*-

import ast
import MySQLdb
from functools import wraps
from flask import Flask, jsonify, g, request, make_response
from config import DEBUG
from sae.storage import Bucket
from time import time

app = Flask(__name__)
app.debug = DEBUG
app.config.from_pyfile("config.py")

bucket = Bucket("avatar")

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
    query = "select last_insert_id()"
    cursor.execute(query)
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

    query = "select userId, password, userName from User where email = %s"
    cursor = g.db.cursor()
    cursor.execute(query, (account,))
    record = cursor.fetchone()

    if record is None:
        return jsonify(state=3, error="user does not exist")

    if password != record[1]:
        return jsonify(state=2, error="incorrect password")

    return jsonify(state=1, userId=record[0], userName=record[2])


@app.route("/user/password", methods=["POST", "OPTIONS"])
@allow_cross_domain
def change_pwd():
    data = parseData()
    email = data.get("email", "")
    oldPwd = data.get("oldpassword", "")
    newPwd = data.get("npassword", "")

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
    query = ("select userName, realName, phoneNum, QQ, location, school \
             from User where userId = %s")
    cursor = g.db.cursor()
    cursor.execute(query, (userId,))
    result = cursor.fetchone()
    dict_res = {}
    dict_res["userName"] = result[0]
    dict_res["realName"] = result[1]
    dict_res["phoneNum"] = result[2]
    dict_res["QQ"] = result[3]
    dict_res["location"] = result[4]
    dict_res["school"] = result[5]

    return jsonify(state=1, result=dict_res)


@app.route("/user", methods=["POST", "OPTIONS"])
@allow_cross_domain
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


@app.route("/item", methods=["POST", "OPTIONS"])
@allow_cross_domain
def create_item():
    userId = request.form.get("userId", None)
    title = request.form.get("title", None)
    categoryId = request.form.get("category", None)
    subcategoryId = request.form.get("subcategory", None)
    price = request.form.get("price", None)
    tradeVenue = request.form.get("tradeVenue", None)
    description = request.form.get("description", None)
    pictureNum = request.form.get("pictureNum", None)
    # TODO: picture uploading
    # pictures
    arguable = request.form.get("arguable", None)
    recency = request.form.get("recency", None)
    delivery = request.form.get("delivery", None)
    postDate = time()

    # cast type
    categoryId = int(categoryId)
    subcategoryId = int(subcategoryId)
    price = float(price)
    pictureNum = int(pictureNum)
    arguable = int(arguable)
    recency = int(recency)
    delivery = int(delivery)

    # TODO: image uploading
    try:
        # get sender name
        cursor = g.db.cursor()
        query = "select userName from User where userId = %s"
        cursor.execute(query, (userId,))
        userName = cursor.fetchone()[0]

        # create new item
        insert = ("insert into Item(\
                userId, userName, name, categoryId, subcategoryId, price,\
                arguable, tradeVenue, recency, description, postDate, delivery,\
                postDate ) values ( \
                %s, %s, %s, %s, %s, %s, \
                %s, %s, %s, %s, %s, %s, %s)")
        params = (userId, userName, title, categoryId, subcategoryId, price,
                  arguable, tradeVenue, recency, description, postDate,
                  delivery, postDate)
        cursor.execute(insert, params)
        g.db.commit()

        # get newly generated item id
        query = ("select last_insert_id()")
        cursor.execute(query)
        result = cursor.fetchone()
        itemId = result[0]

        # create Sell relationship between seller and posted item
        insert = ("insert into Sell(userId, itemId) values(%s, %s)")
        cursor.execute(insert, (userId, itemId))
        g.db.commit()

        # create fallsIn relationship between the category and subcategory
        insert = ("insert into FallsIn(itemId, categoryId, subcategoryId) \
                values(%s, %s, %s)")
        cursor.execute(insert, (itemId, categoryId, subcategoryId))
        g.db.commit()

        return jsonify(state=1)
    except:
        return jsonify(state=0, error="fail to create item")


@app.route("/item/sellingProducts", methods=["GET", "OPTIONS"])
@allow_cross_domain
def get_selling_products():

    # get arguements
    userId = request.args.get("userId", None)
    if not userId:
        return jsonify(state=0, error="no arguement passed")

    # retrieve data
    cursor = g.db.cursor()
    query = ("select itemId, title, state from Item and Sell \
             where Sell.userId = %s and Sell.itemId = Item.itemId")
    cursor.execute(query, (userId,))
    items = cursor.fetchall()

    # return values
    return jsonify(state=1, items=items)


@app.route("/item", methods=["GET, OPTIONS"])
@allow_cross_domain
def get_item_info():
    itemId = request.args.get("itemId", None)
    if not itemId:
        return jsonify(state=0, error="no arguement passed")

    # get item info
    # TODO: item image
    cursor = g.db.cursor()
    query = ("select * from Item where itemId = %s")
    cursor.execute(query, (itemId,))
    item_record = cursor.fetchone()

    # get category


    # package data
    return jsonify()


@app.route("/item/collect", methods=["POST", "OPTIONS"])
@allow_cross_domain
def collect_item():
    itemId = request.form.get("itemId", None)
    userId = request.form.get("userId", None)
    collectTime = time()

    if not itemId or not userId:
        return jsonify(state=0, error="no arguement passed")

    cursor = g.db.cursor()
    insert = ("insert into Collect(userId, itemId, collectTime) \
              values(%s, %s, %s)")
    cursor.execute(insert, (userId, itemId, collectTime))
    g.db.commit()

    return jsonify(state=1)


@app.route("/item/collections", methods=["GET", "OPTIONS"])
@allow_cross_domain
def get_collected_items():
    userId = request.args.get("userId", None)
    if not userId:
        return jsonify(state=0, error="no arguement passed")

    cursor = g.db.cursor()
    # query correctness unsure
    query = ("select itemId, title from Item and Collect \
             where Collect.userId = %s and Collect.itemId = Item.itemId")
    cursor.execute(query, (userId))
    items = cursor.fetchall()

    return jsonify(state=1, items=items)


@app.route("/test", methods=["POST", "OPTIONS"])
@allow_cross_domain
def test():
    return jsonify(state=1)


if __name__ == "__main__":
    app.run()
