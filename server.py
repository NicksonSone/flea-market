# -*- coding: utf-8 -*-

import ast
import MySQLdb
import urllib
from functools import wraps
from flask import Flask, jsonify, g, request, make_response
from config import DEBUG, lock
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


def getSubCategory(categoryId):
    firstSubId, lastSubId = getSubRange(categoryId)
    cursor = g.db.cursor()
    query = "select * from SubCategory where subcategoryId between %s and %s"
    cursor.execute(query, (firstSubId, lastSubId))
    subcategories = cursor.fetchall()
    return subcategories


def addPriceCondition(query, categoryId, price):
    if 2 <= categoryId and categoryId <= 4:
        if price == 0:
            query += "and price < 100 "
        elif price == 1:
            query += "and price >= 100 and price < 300 "
        elif price == 2:
            query += "and price >= 300 and price < 500 "
        elif price == 3:
            query += "and price >= 500 and price < 1000 "
        else:
            query += "and price >= 100 "
    else:
        if price == 0:
            query += "and price < 10 "
        elif price == 1:
            query += "and price >= 10 and price < 30 "
        elif price == 2:
            query += "and price >= 30 and price < 50 "
        elif price == 3:
            query += "and price >= 50 and price < 80 "
        elif price == 4:
            query += "and price >= 80 and price > 100 "
        elif price == 5:
            query += "and price >= 100 "

    return query


def addSortingCondition(query, sorting):
    if sorting == 2:
        query += "order by postDate DESC "
    elif sorting == 3:
        query += "order by price ASC "
    elif sorting == 4:
        query += "order by price DESC "

    return query


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
    query = ("select itemId, title, postDate from Item \
             where subcategoryId = 11 \
             order by postDate limit 5")
    cursor.execute(query)

    # change to list for modification
    foreignBooks = list(cursor.fetchall())
    for i in xrange(len(foreignBooks)):
        foreignBooks[i] = list(foreignBooks[i])
        foreignBooks[i][2] = datetimeToTimeElement(foreignBooks[i][2])

    # latest professional material
    query = ("select itemId, title, postDate from Item \
             where subcategoryId = 14 \
             order by postDate limit 5")
    cursor.execute(query)
    professionalMaterials = list(cursor.fetchall())
    for i in xrange(len(professionalMaterials)):
        professionalMaterials[i] = list(professionalMaterials[i])
        professionalMaterials[i][2] = \
            datetimeToTimeElement(professionalMaterials[i][2])

    # latest bikecycles
    query = ("select itemId, title, postDate from Item \
             where subcategoryId = 21 \
             order by postDate limit 5")
    cursor.execute(query)
    bikecycles = list(cursor.fetchall())
    for i in xrange(len(bikecycles)):
        bikecycles[i] = list(bikecycles[i])
        bikecycles[i][2] = datetimeToTimeElement(bikecycles[i][2])

    # latest appliances
    query = ("select itemId, title, postDate from Item \
             where subcategoryId = 41 \
             order by postDate limit 5")
    cursor.execute(query)
    appliances = list(cursor.fetchall())
    for appliance in appliances:
        appliance = list(appliance)
        appliance[2] = datetimeToTimeElement(appliance[2])

    # new product list
    query = ("select itemId, title, postDate from Item \
             order by postDate DESC limit 10")
    cursor.execute(query)
    newProducts = list(cursor.fetchall())
    for i in xrange(len(newProducts)):
        newProducts[i] = list(newProducts[i])
        newProducts[i][2] = datetimeToTimeElement(newProducts[i][2])

    # books
    query = ("select itemId, title, postDate from Item \
             where categoryId = 1 \
             order by postDate DESC limit 10 ")
    cursor.execute(query)
    books = list(cursor.fetchall())
    for i in xrange(len(books)):
        books[i] = list(books[i])
        books[i][2] = datetimeToTimeElement(books[i][2])

    # transportation
    query = ("select itemId, title, postDate from Item \
             where categoryId =  2 \
             order by postDate DESC limit 10")
    cursor.execute(query)
    transportations = list(cursor.fetchall())
    for i in xrange(len(transportations)):
        transportations[i] = list(transportations[i])
        transportations[i][2] = datetimeToTimeElement(transportations[i][2])

    # groceries
    query = ("select itemId, title, postDate from Item \
             where categoryId =3 \
             order by postDate DESC limit 10")
    cursor.execute(query)
    groceries = list(cursor.fetchall())
    for i in xrange(len(groceries)):
        groceries[i] = list(groceries[i])
        groceries[i][2] = datetimeToTimeElement(groceries[i][2])

    # entertainments
    query = ("select itemId, title, postDate from Item \
             where categoryId =3 \
             order by postDate DESC limit 10 ")
    cursor.execute(query)
    entertainments = list(cursor.fetchall())
    for i in xrange(len(entertainments)):
        entertainments[i] = list(entertainments[i])
        entertainments[i][2] = datetimeToTimeElement(entertainments[i][2])

    return jsonify(state=1, categoryList=categoryList,
                   subCategoryList=subCategoryList,
                   newProducts=newProducts, bikecycles=bikecycles,
                   foreignBooks=foreignBooks, appliances=appliances,
                   professionalMaterials=professionalMaterials, books=books,
                   groceries=groceries, transportations=transportations,
                   entertainments=entertainments)


@app.route("/page/browsing", methods=['GET', 'OPTIONS'])
@allow_cross_domain
def browsing_page():
    # return list of subcategory and a list of products
    # sort the list if sorting option provided
    categoryId = int(request.args.get("categoryId", 1))
    subcategoryId = int(request.args.get("subcategoryId", -1))

    page = int(request.args.get("page", 1))
    numberItems = int(request.args.get("numberItems", 10))

    recency = int(request.args.get("recency", -1))
    price = int(request.args.get("price", -1))
    tradeVenue = int(request.args.get("tradeVenue", -1))
    sorting = int(request.args.get("sorting", 1))

    # get list of subcategories
    subcategories = getSubCategory(categoryId)

    # form query and parameter for retrieving products
    query = ("select title, tradeVenue, postDate, price, recency from Item"
             " where categoryId = %s ")
    parameters = (categoryId,)
    if subcategoryId is not -1:
        # trailing space is necessary for query assembly
        query += "and subcategoryId = %s "
        parameters += (subcategoryId,)

    if recency is not -1:
        query += "and recency = %s "
        parameters += (recency,)

    if tradeVenue is not -1:
        query += "and tradeVenue = %s "
        parameters += (tradeVenue,)

    if price is not -1:
        query = addPriceCondition(query, categoryId, price)

    if sorting != 1:
        query = addSortingCondition(query, sorting)

    query += "limit %s offset %s "
    parameters += (numberItems, (page-1) * numberItems)

    # get products
    cursor = g.db.cursor()
    cursor.execute(query, parameters)
    products = list(cursor.fetchall())

    for i in xrange(len(products)):
        products[i] = list(products[i])
        products[i][2] = datetimeToTimeElement(products[i][2])

    # number of products under specific category
    count = ("select count(itemId) from FallsIn where categoryId = %s")
    parameters = (categoryId,)

    if subcategoryId is not -1:
        query += "and subcategoryId = %s"
        parameters += (subcategoryId,)

    cursor = g.db.cursor()
    cursor.execute(count, parameters)
    productsNum = cursor.fetchall()[0]

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
    categoryId = int(request.form.get("categoryId", 0))
    subcategoryId = int(request.form.get("subcategoryId", 0))
    arguable = int(request.form.get("arguable", 0))
    recency = int(request.form.get("recency", 0))
    delivery = int(request.form.get("delivery", 0))
    price = float(request.form.get("price", 0.0))
    tradeVenue = int(request.form.get("tradeVenue", 0))
    title = request.form.get("title", "default")





    title = urllib.unquote(title).decode("utf-8")
    return jsonify(title=title)







    description = request.form.get("description", "description")
    picArray = request.form.getlist("picArray[]")
    postDate = datetime.now()

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
            %s, %s, %s, %s, %s, %s\
            )")
    params = (userId, userName, title, categoryId, subcategoryId, price,
              arguable, tradeVenue, recency, description, delivery, postDate,
              )
    cursor.execute(insert, params)
    g.db.commit()

    query = ("select last_insert_id() from Item")
    cursor.execute(query)
    result = cursor.fetchone()
    itemId = result[0]


    # insert image url into database
    update = ("update Item set ")
    query = (" where itemId = %s")

    # forming insertion statement
    numImages = len(picArray)
    parameters = ()
    for i in xrange(numImages):
        update += "image" + str(i+1) + " = %s"
        parameters += (picArray[i],)
        if i < numImages - 1:
            update += ","
    update += query
    parameters += (itemId,)
    cursor.execute(update, parameters)
    g.db.commit()

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

    # decode Chinese character
    # item[3] = urllib.unquote(item[3]).decode("utf-8")

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
    query = ("select Item.itemId, Item.title, Item.state, Item.image1 \
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
    global lock
    if request.method == 'POST':
        image = request.files['fileList']
        while lock == 1:
            pass
        lock = 1
        if image:
            bucket = Bucket("avatar")
            numObejcts = int(bucket.stat()["objects"])
            imageId = str(numObejcts + 1) + ".jpg"
            bucket.put_object(imageId, image.stream)
            url = bucket.generate_url(imageId)

            lock = 0

            return url
        lock = 0
    return jsonify(error="fail to upload image")


if __name__ == "__main__":
    app.run()
