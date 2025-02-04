from app import mysql
from flask import g

def getConnection():
    if 'conn' not in g:
        g['conn'] = mysql.connect()
    
    return g['conn']

def closeConnection(e=None):
    conn = g.pop('conn', None)
    
    if conn is not None:
        conn.close()