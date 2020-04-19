#!/usr/bin/env python

import pymysql
from craft_api import settings

# test connection to mysql database

connection = pymysql.connect(host=settings.MYSQL_DATABASE_HOST,
                             user=settings.MYSQL_DATABASE_USER,
                             password=settings.MYSQL_DATABASE_PASSWORD,
                             db=settings.MYSQL_DATABASE_DB,
                             cursorclass=pymysql.cursors.DictCursor)

try:
	with connection.cursor() as cursor:
		while True:
			sql = input("SQL > ")
			cursor.execute(sql)
			result = cursor.fetchall()
			print(result)

finally:
    connection.close()

