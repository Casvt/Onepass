#-*- coding: utf-8 -*-

from sqlite3 import Connection, Cursor, Row, connect
from threading import current_thread
from typing import Union
from urllib import request

from flask import g

__DATABASE_VERSION__ = 1

class Singleton(type):
	_instances = {}
	def __call__(cls, *args, **kwargs):
		i = f'{cls}{current_thread()}'
		if i not in cls._instances:
			cls._instances[i] = super(Singleton, cls).__call__(*args, **kwargs)
			
		return cls._instances[i]

class DBConnection(Connection, metaclass=Singleton):
	file = ''
	
	def __init__(self, timeout: float) -> None:
		super().__init__(self.file, timeout=timeout)
		super().cursor().execute("PRAGMA foreign_keys = ON;")
		return

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
	try:
		cursor = g.cursor
	except AttributeError:
		db = DBConnection(timeout=20.0)
		cursor = g.cursor = Extended_Cursor(db)
		
	if output_type is dict:
		cursor.row_factory = Row
	else:
		cursor.row_factory = None
	return g.cursor

def close_db(e=None) -> None:
	"""Savely closes the database connection
	"""	
	try:
		cursor = g.cursor
		db = cursor.connection
		cursor.close()
		delattr(g, 'cursor')
		db.commit()
	except AttributeError:
		pass
	return

def migrate_db(current_db_version: int) -> None:
	"""
	Migrate a Onepass database from it's current version
	to the newest version suppoted by the Onepass version installed.
	"""
	print('Migrating database to newer version...')
	
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
			password BLOB,
			
			FOREIGN KEY (user_id) REFERENCES users(id)
		);
		CREATE TABLE IF NOT EXISTS most_used_passwords(
			password VARCHAR(255) UNIQUE NOT NULL
		);
		CREATE TABLE IF NOT EXISTS config(
			key VARCHAR(255) PRIMARY KEY,
			value TEXT NOT NULL
		);
	""")
	
	cursor.execute("""
		INSERT OR IGNORE INTO config(key, value)
		VALUES ('database_version', ?);
		""",
		(__DATABASE_VERSION__,)
	)
	current_db_version = int(cursor.execute("SELECT value FROM config WHERE key = 'database_version' LIMIT 1;").fetchone()[0])
	if current_db_version < __DATABASE_VERSION__:
		migrate_db(current_db_version)
		cursor.execute(
			"UPDATE config SET value = ? WHERE key = 'database_version' LIMIT 1;",
			(__DATABASE_VERSION__,)
		)
	
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
