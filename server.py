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

class Protocol:
    class CategoryList:
        idMapping = {
            "书本教材": 1,
            "交通工具": 2,
            "日常用品": 3,
            "数码电器": 4,
            "文体活动": 5,
        }

    class SubCategoryList:
        idMapping = {
            "留学资料": 11,
            "考研复习": 12,
            "日常用品": 3,
            "数码电器": 4,
            "文体活动": 5,
        }


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
        allow_headers = "Referer,Accept,Origin,User-Agent, Content-Type, \
            X_FILENAME"
        rst.headers['Access-Control-Allow-Headers'] = allow_headers
        return rst
    return wrapper_fun


def parseData():
    data = list(request.form.iterkeys())
    if not data:
        return None
    data = ast.literal_eval(data[0])
    return data


def getSubRange(categoryId):
    if categoryId == 1:
        firstSubId = 11
        lastSubId = 17
    elif categoryId == 2:
        firstSubId = 21
        lastSubId = 22
    elif categoryId == 3:
        firstSubId = 31
        lastSubId = 36
    elif categoryId == 4:
        firstSubId = 41
        lastSubId = 46
    else:
        firstSubId = 51
        lastSubId = 56
    return firstSubId, lastSubId


def datetimeToTimeElement(datetime):
    return list(datetime.timetuple())


@app.route("/page/front", methods=['GET', 'OPTIONS'])
@allow_cross_domain
def front_page():
    cursor = g.db.cursor()

    # get category list
    query = ("select * from Category")
    cursor.execute(query)
    categoryList = cursor.fetchall()

    # get subcategory list
    query = ("select * from SubCategory")
    cursor.execute(query)
    subCategoryList = cursor.fetchall()

    # latest foreign education materials
    query = ("select * from Item \
             where subcategoryId = 11 \
             order by postDate limit 5")
    cursor.execute(query)
    foreignBooks = list(cursor.fetchall())
    for book in foreignBooks:
        book[11] = datetimeToTimeElement(book[11])

    # latest professional material
    query = ("select * from Item \
             where subcategoryId = 14 \
             order by postDate limit 5")
    cursor.execute(query)
    professionalMaterials = cursor.fetchall()
    for material in professionalMaterials:
        material[11] = datetimeToTimeElement(material[11])

    # latest bikecycles
    query = ("select * from Item \
             where subcategoryId = 21 \
             order by postDate limit 5")
    cursor.execute(query)
    bikecycles = cursor.fetchall()
    for bike in bikecycles:
        bike[11] = datetimeToTimeElement(bike[11])

    # latest appliances
    query = ("select * from Item \
             where subcategoryId = 41 \
             order by postDate limit 5")
    cursor.execute(query)
    appliances = cursor.fetchall()
    for appliance in appliances:
        appliance[11] = datetimeToTimeElement(appliance[11])

    # new product list
    query = ("select * from Item order by postDate DESC limit 10")
    cursor.execute(query)
    newProducts = cursor.fetchall()

    return jsonify(categoryList=categoryList, subCategoryList=subCategoryList,
                   newProducts=newProducts, bikecycles=bikecycles,
                   foreignBooks=foreignBooks, appliances=appliances,
                   professionalMaterials=professionalMaterials)


@app.route("/page/browsing", methods=['GET', 'OPTIONS'])
@allow_cross_domain
def browsing_page():
    # return list of subcategory and a list of products
    # sort the list if sorting option provided
    firstItemId = request.args.get("firstItemId", 1)
    numberItems = request.args.get("numberItems", 10)
    categoryId = request.args.get("categoryId", 1)
    subcategoryId = request.args.get("subcategoryId", None)
    sorting = request.args.get("sorting", 1)

    # get list of subcategories
    firstSubId, lastSubId = getSubRange(categoryId)
    cursor = g.db.cursor()
    query = "select * from SubCategory where subcategoryId between %s and %s"
    cursor.execute(query, (firstSubId, lastSubId))
    subcategories = cursor.fetchall()

    # form query and parameter for retrieving products
    query = ("select title, tradeVenue, postDate, price from Item"
             " where categoryId = %s")
    parameters = (categoryId,)
    if subcategoryId is not None:
        query += "and subcategoryId = %s"
        parameters += (subcategoryId,)

    if sorting == 2:
        query += "order by postDate DESC"
    elif sorting == 3:
        query += "order by price ASC"
    elif sorting == 4:
        query += "order by price DESC"

    query += "limit %s offset %s"
    parameters += (numberItems, firstItemId)

    # get products
    cursor = g.db.cursor()
    cursor.execute(query, parameters)
    products = cursor.fetchall()

    # transform item objects
    for item in products:
        item[3] = datetimeToTimeElement(item[3])

    # number of products under specific category
    count = ("select count(itemId) from FallsIn where categoryId = %s")
    parameters = (categoryId,)

    if subcategoryId is not None:
        query += "and subcategoryId = %s"
        parameters += (subcategoryId,)

    cursor = g.db.cursor()
    cursor.execute(count, parameters)
    productsNum = cursor.fetchall()

    return jsonify(state=1, subcategories=subcategories, products=products,
                   productsNum=productsNum)


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


@app.route("/item", methods=["GET", "OPTIONS"])
@allow_cross_domain
def create_item():
    userId = int(request.args.get("userId", 0))
    categoryId = int(request.args.get("categoryId", "default"))
    subcategoryId = int(request.args.get("subcategoryId", 0))
    arguable = int(request.args.get("arguable", 0))
    recency = int(request.args.get("recency", 0))
    delivery = int(request.args.get("delivery", 0))
    price = float(request.args.get("price", 0.0))
    title = request.args.get("title", "default")
    tradeVenue = request.args.get("tradeVenue", "default")
    description = request.args.get("description", "description")
    # image upload
    postDate = datetime.now()

    # TODO: image uploading
    # try:
    #   get sender name
    cursor = g.db.cursor()
    query = "select userName from User where userId = %s"
    cursor.execute(query, (userId,))
    userName = cursor.fetchone()[0]

    # create new item
    insert = ("insert into Item(\
            userId, userName, title, categoryId, subcategoryId, price,\
            arguable, tradeVenue, recency, description, delivery, postDate\
            ) values ( \
            %s, %s, %s, %s, %s, %s, \
            %s, %s, %s, %s, %s, %s)")
    params = (userId, userName, title, categoryId, subcategoryId, price,
              arguable, tradeVenue, recency, description, delivery, postDate)
    cursor.execute(insert, params)
    return jsonify(r="here")
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

    # transform datetime object to list of date elements, to be josnifiable
    item = list(cursor.fetchone())
    item[11] = datetimeToTimeElement(item[11])

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


@app.route("/image/upload", methods=["POST", "OPTIONS"])
@allow_cross_domain
def image_upload():
    if request.method == 'POST':
        image = request.files['fileList']
        if image:
            bucket = Bucket("avatar")
            bucket.put_object(image.filename, image.stream)
            url = bucket.generate_url(image.filename)

            return jsonify(state=url)
    return jsonify(error="fail to upload image")


if __name__ == "__main__":
    app.run()
