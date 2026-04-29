import mysql.connector

db = mysql.connector.connect(
    host="gateway01.us-east-1.prod.aws.tidbcloud.com",
    user="4BtnYynyA2LKuR9.root",
    password="ehCOCdwW7MinZKIj",
    database="sys"
)

cursor = db.cursor(dictionary=True)