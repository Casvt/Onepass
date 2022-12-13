#-*- coding: utf-8 -*-

from sqlite3 import Cursor, Row, connect
from typing import Union
from urllib import request

from flask import g

ONEPASS_DB_FILE = 'Onepass.db'

class Extended_Cursor(Cursor):
	"""Extended version of the sqlite3 Cursor object. Adds the exists function.

	Args:
		Cursor (_type_): The Cursor instance to use
	"""	
	def __init__(self, connection):
		super().__init__(connection)
		
	def exists(self, __sql: str, __parameters: Union[list, tuple]) -> bool:
		"""Check if an entry exists in a database table

		Args:
			__sql (str): The SQL command that should return the entry
			__parameters (Union[list, tuple]): The values of the parameters of the command

		Returns:
			bool: Wether or not a row was returned
		"""		
		return self.execute(__sql, __parameters).fetchone() is not None

def get_db(output_type: Union[dict, tuple]=tuple) -> Extended_Cursor:
	"""Get a database cursor instance. Coupled to Flask's g.

	Args:
		output_type (Union[dict, tuple], optional): The type of output: a tuple or dictionary with the row values. Defaults to tuple.

	Returns:
		Extended_Cursor: The Cursor instance to use
	"""	
	if not hasattr(g, 'cursor'):
		db = connect(ONEPASS_DB_FILE, timeout=20.0)
		g.cursor = Extended_Cursor(db)
		if output_type == dict:
			g.cursor.row_factory = Row
	else:
		if output_type == tuple and g.cursor.row_factory == Row:
			g.cursor.row_factory = None
		elif output_type == dict and g.cursor.row_factory is None:
			g.cursor.row_factory = Row

	return g.cursor

def close_db(e=None) -> None:
	"""Savely closes the database connection
	"""	
	if hasattr(g, 'cursor'):
		db = g.cursor.connection
		g.cursor.close()
		delattr(g, 'cursor')
		db.commit()
		db.close()
	return

def setup_db() -> None:
	"""Setup the database
	"""
	cursor = get_db()

	cursor.executescript("""
		CREATE TABLE IF NOT EXISTS users(
			id INTEGER PRIMARY KEY,
			username VARCHAR(255) UNIQUE NOT NULL,
			salt VARCHAR(40) NOT NULL,
			encrypted_key VARCHAR(255) NOT NULL
		);
		CREATE TABLE IF NOT EXISTS vault(
			id INTEGER PRIMARY KEY,
			user_id INTEGER,
			title BLOB,
			url BLOB,
			username BLOB,
			password BLOB
		);
		CREATE TABLE IF NOT EXISTS most_used_passwords(
			password VARCHAR(255) UNIQUE NOT NULL
		);
	""")
	cursor.execute("SELECT password FROM most_used_passwords LIMIT 1;")
	if cursor.fetchone() is None:
		cursor.executemany(
			"INSERT OR IGNORE INTO most_used_passwords VALUES (?)",
			map(
				lambda p: (p,),
				request.urlopen(
					'https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt'
				).read().decode().split('\n')
			)
		)

	return
