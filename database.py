import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="app_db"
)

cursor = db.cursor(dictionary=True)