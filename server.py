# -*- coding: utf-8 -*-

import ast
import MySQLdb
from functools import wraps
from flask import Flask, jsonify, g, request, make_response
from config import DEBUG
from sae.storage import Bucket
from datetime import datetime

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
    data = list(request.form.iterkeys())
    if not data:
        return None
    data = ast.literal_eval(data[0])
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
    signUpDate = datetime.now()

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
    account = data.get("account", None)
    password = data.get("password", None)

    if not account or not password:
        return jsonify(state=0)

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
    userId = int(data.get("userId", ""))
    oldPwd = data.get("oldPwd", "")
    newPwd = data.get("newPwd", "")

    cursor = g.db.cursor()
    update = "update User set password = %s where userId = %s and password = %s"
    row = cursor.execute(update, (newPwd, userId, oldPwd))

    if not row:
        return jsonify(state=0, error="incorrect password")

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
    userId = int(request.form.get("userId", 0))
    categoryId = int(request.form.get("category", 0))
    subcategoryId = int(request.form.get("subcategory", 0))
    arguable = int(request.form.get("arguable", 0))
    recency = int(request.form.get("recency", 0))
    delivery = int(request.form.get("delivery", 0))
    price = float(request.form.get("price", 0.0))
    title = request.form.get("title", None)
    tradeVenue = request.form.get("tradeVenue", None)
    description = request.form.get("description", None)
    # image upload
    postDate = datetime.now()

    return jsonify(userId=userId, title=title, categoryId=categoryId,
                   subcategoryId=subcategoryId, price=price,
                   tradeVenue=tradeVenue)

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


@app.route("/item", methods=["GET", "OPTIONS"])
@allow_cross_domain
def get_item_info():
    itemId = int(request.args.get("itemId", 0))
    if not itemId:
        return jsonify(state=0, error="no arguement passed")

    # get item info
    cursor = g.db.cursor()
    query = ("select * from Item where itemId = %s")
    cursor.execute(query, (itemId,))
    item = cursor.fetchone()

    # get seller info
    userId = item[1]
    query = ("select userId, userName, phoneNum, QQ from User \
             where userId = %s")
    cursor.execute(query, (userId,))
    user = cursor.fetchone()

    return jsonify(state=1, item=item, user=user)


@app.route("/item/sellingProducts", methods=["GET", "OPTIONS"])
@allow_cross_domain
def get_selling_products():

    # get arguements
    userId = request.args.get("userId", None)
    if not userId:
        return jsonify(state=0, error="no arguement passed")

    # retrieve data
    cursor = g.db.cursor()
    query = ("select Item.itemId, Item.title, Item.state, Item.image1\
             from Item, Sell \
             where Sell.userId = %s and Sell.itemId = Item.itemId")
    cursor.execute(query, (userId,))
    items = cursor.fetchall()

    # return values
    return jsonify(state=1, items=items)


@app.route("/item/collect", methods=["POST", "OPTIONS"])
@allow_cross_domain
def collect_item():
    data = parseData()
    itemId = int(data.get("itemId", 0))
    userId = int(data.get("userId", 0))
    collectTime = datetime.time()

    if not itemId or not userId:
        return jsonify(state=0, error="no arguement passed")

    cursor = g.db.cursor()
    insert = ("insert ignore into Collect(userId, itemId, collectTime) \
              values(%s, %s, %s)")
    cursor.execute(insert, (userId, itemId, collectTime))
    g.db.commit()

    return jsonify(state=1)


@app.route("/item/removeCollection", methods=["POST", "OPTIONS"])
@allow_cross_domain
def remove_collection():
    data = parseData()
    itemId = int(data.get("itemId", 0))
    userId = int(data.get("userId", 0))

    if not itemId or not userId:
        return jsonify(state=0, error="no arguement passed")

    try:
        cursor = g.db.cursor()
        delete = ("delete from Collect where userId = %s and itemId = %s")
        cursor.execute(delete, (userId, itemId))
        g.db.commit()
    except:
        g.db.rollback()
        return jsonify(state=0)

    return jsonify(state=1)


@app.route("/item/collections", methods=["GET", "OPTIONS"])
@allow_cross_domain
def get_collected_items():
    userId = request.args.get("userId", None)
    if not userId:
        return jsonify(state=0, error="no arguement passed")

    userId = int(userId)
    cursor = g.db.cursor()
    # query correctness unsure
    query = ("select Item.itemId, Item.title, Item.image1 from Item, Collect \
             where Collect.userId = %s and Collect.itemId = Item.itemId")
    cursor.execute(query, (userId,))
    items = cursor.fetchall()

    return jsonify(state=1, items=items)


@app.route("/test", methods=["POST", "OPTIONS"])
@allow_cross_domain
def test_image_upload():
    post = request.form
    return jsonify(post=post)
    filed = request.files
    data = request.get_json()
    d = request.json
    a = request.data
    bucket = Bucket("avatar")
    url = {}
    if post:
        bucket.put_object("post", post)
        url["post"] = bucket.generate_url("post")
    if filed:
        bucket.put_object("filed", filed)
        url["filed"] = bucket.generate_url("filed")
    if data:
        bucket.put_object("data", data)
        url["data"] = bucket.generate_url("data")
    if d:
        bucket.put_object("d", d)
        url["d"] = bucket.generate_url("d")
    if a:
        bucket.put_object("a", a)
        url["a"] = bucket.generate_url("a")

    return jsonify(state=url)


@app.route("/testTime", methods=["POST", "OPTIONS"])
@allow_cross_domain
def test_time():
    cnt = 10
    now = datetime.now()

    cursor = g.db.cursor()
    cursor.execute("insert into test(test, time) values(%s, %s)", (cnt, now))
    cursor.execute("select time from test where test = %s", (cnt,))
    time = cursor.fetchone()[0]
    l = list(time.timetuple())

    return jsonify(time=l)


if __name__ == "__main__":
    app.run()
