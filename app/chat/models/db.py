from app import mysql
from flask import g

def getConnection():
    if 'db' not in g:
        g.db = mysql.get_db()
    
    return g.db

def closeConnection(e=None):
    conn = g.pop('db', None)
    
    if conn is not None:
        conn.close()

def db_insert(sql, args):
    try:
        conn = getConnection()
        cur = conn.cursor()
        cur.execute(sql, args)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Database insertion error: ", e)
    finally:
        closeConnection()