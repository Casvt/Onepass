#-*- coding: utf-8 -*-

from flask import g
from sqlite3 import connect as db_connect, Row
from urllib import request

ONEPASS_DB_FILE = 'Onepass.db'

def get_db(output_type='tuple'):
	if not (hasattr(g, 'db') and hasattr(g, 'cursor')):
		g.db = db_connect(ONEPASS_DB_FILE, timeout=20.0)
		g.cursor = g.db.cursor()
		if output_type == 'dict':
			g.cursor.row_factory = Row
	if output_type == 'tuple' and g.cursor.row_factory == Row:
		g.cursor.row_factory = None
	elif output_type == 'dict' and g.db.row_factory == None:
		g.cursor.row_factory = Row
	return g.cursor

def close_db(e=None):
	if hasattr(g, 'db') and hasattr(g, 'cursor'):
		g.cursor.close()
		delattr(g, 'cursor')
		g.db.commit()
		g.db.close()
		delattr(g, 'db')
	return

def setup_db() -> None:
	"""Setup the database
	"""
	db = db_connect(ONEPASS_DB_FILE)
	cursor = db.cursor()

	cursor.executescript("""
		CREATE TABLE IF NOT EXISTS users(
			id INTEGER PRIMARY KEY,
			username VARCHAR(254) UNIQUE NOT NULL,
			salt VARCHAR(254) NOT NULL,
			key VARCHAR(254) NOT NULL
		);
		CREATE TABLE IF NOT EXISTS most_used_passwords(
			password VARCHAR(255) UNIQUE NOT NULL
		);
	""")
	cursor.execute("SELECT password FROM most_used_passwords LIMIT 1;")
	if cursor.fetchone() is None:
		cursor.executemany(
			"INSERT OR IGNORE INTO most_used_passwords VALUES (?)",
			map(lambda p: (p,), request.urlopen('https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt').read().decode().split('\n'))
		)

	cursor.close()
	db.commit()
	db.close()
	return
