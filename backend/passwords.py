#-*- coding: utf-8 -*-

from os.path import dirname, join
from urllib import request
from hashlib import sha1
from typing import List

from backend.custom_exceptions import BadPassword, IdNotFound
from backend.security import encrypt, decrypt
from backend.db import get_db

def add_password(
	hash_encrypted_key: str, raw_key: bytes,
	title: str, url: str=None, username: str=None, password: str=None
) -> int:
	"""Add a password to the vault

	Args:
		hash_encrypted_key (str): The hash of the encrypted key of the user
		raw_key (bytes): The decrypted key of the user
		title (str): The title of the entry
		url (str, optional): The url of the entry. Defaults to None.
		username (str, optional): The username of the entry. Defaults to None.
		password (str, optional): The password of the entry. Defaults to None.

	Returns:
		int: The id of the new entry
	"""
	insert_keys = ['title']
	insert_values = [encrypt(raw_key, title.encode('utf-8'))]
	del title
	if url != None:
		insert_keys.append('url')
		insert_values.append(encrypt(raw_key, url.encode('utf-8')))
		del url
	if username != None:
		insert_keys.append('username')
		insert_values.append(encrypt(raw_key, username.encode('utf-8')))
		del username
	if password != None:
		insert_keys.append('password')
		insert_values.append(encrypt(raw_key, password.encode('utf-8')))
		del password
	del raw_key

	cursor = get_db()

	cursor.execute(f"""
		INSERT INTO `{hash_encrypted_key}`({','.join(insert_keys)})
		VALUES ({','.join(['?'] * len(insert_values))})
	""", insert_values)
	id = cursor.lastrowid

	return id

def get_password(
	hash_encrypted_key: str, raw_key: bytes,
	id: int
) -> dict:
	"""Get a password from the vault

	Args:
		hash_encrypted_key (str): The hash of the encrypted key of the user
		raw_key (bytes): The decrypted key of the user
		id (int): The id of the password entry

	Raises:
		IdNotFound: No password entry found with that id in the vault

	Returns:
		dict: title, url, username and password in decrypted form
	"""
	cursor = get_db(output_type='dict')

	#check if password exists
	cursor.execute(f"SELECT id, title, url, username, password FROM `{hash_encrypted_key}` WHERE id = ?", (id,))
	result = cursor.fetchone()
	if result == None:
		raise IdNotFound

	info = {k: decrypt(raw_key, bytes(v)).decode() if not (k == 'id' or v == None) else v for k, v in dict(result).items()}
	return info

def edit_password(
	hash_encrypted_key: str, raw_key: bytes,
	id: int,
	title: str=None, url: str=None, username: str=None, password: str=None,
) -> dict:
	"""Edit a password entry in the vault

	Args:
		hash_encrypted_key (str): The hash of the encrypted key of the user
		raw_key (bytes): The decrypted key of the user
		id (int): The id of the password entry
		title (str, optional): The new value for the title. Defaults to None.
		url (str, optional): The new value for the url. Defaults to None.
		username (str, optional): The new value for the username. Defaults to None.
		password (str, optional): The new value for the password. Defaults to None.

	Raises:
		IdNotFound: No password entry found with that id in the vault

	Returns:
		dict: The (new) info of the password entry
	"""
	cursor = get_db()

	#check if password exists
	cursor.execute(f"SELECT id FROM `{hash_encrypted_key}` WHERE id = ?", (id,))
	if cursor.fetchone() == None:
		raise IdNotFound

	insert_keys = []
	insert_values = []

	if title != None:
		insert_keys.append('title = ?')
		insert_values.append(encrypt(raw_key, title.encode('utf-8')))
		del title
	if url != None:
		insert_keys.append('url = ?')
		insert_values.append(encrypt(raw_key, url.encode('utf-8')))
		del url
	if username != None:
		insert_keys.append('username = ?')
		insert_values.append(encrypt(raw_key, username.encode('utf-8')))
		del username
	if password != None:
		insert_keys.append('password = ?')
		insert_values.append(encrypt(raw_key, password.encode('utf-8')))
		del password

	cursor.execute(f"""
		UPDATE `{hash_encrypted_key}`
		SET {','.join(insert_keys)}
		WHERE id = ?
	""", insert_values + [id])

	return get_password(hash_encrypted_key, raw_key, id=id)

def delete_password(
	hash_encrypted_key: str,
	id: int,
) -> None:
	"""Remove a password entry from the vault

	Args:
		hash_encrypted_key (str): The hash of the encrypted key of the user
		id (int): The id of the password entry

	Raises:
		IdNotFound: No password entry found with that id in the vault

	Returns:
		None: Password entry successfully removed
	"""
	cursor = get_db()

	cursor.execute(f"SELECT * FROM `{hash_encrypted_key}` WHERE id = ?", (id,))
	if cursor.fetchone() == None:
		return IdNotFound

	cursor.execute(f"DELETE FROM `{hash_encrypted_key}` WHERE id = ?", (id,))

	return

def list_passwords(
	hash_encrypted_key: str, raw_key: bytes,
) -> List[dict]:
	"""List all passwords in the vault

	Args:
		hash_encrypted_key (str): The hash of the encrypted key of the user
		raw_key (bytes): The decrypted key of the user

	Returns:
		list: The id, title and username of every password entry
	"""
	cursor = get_db(output_type='dict')

	cursor.execute(f"SELECT id, title, username FROM `{hash_encrypted_key}`;")
	return sorted([{k: decrypt(raw_key, bytes(v)).decode() if not (k == 'id' or v == None) else v for k, v in dict(e).items()} for e in cursor.fetchall()], key=lambda i: (i['title'], i['username']))

def search_passwords(
	hash_encrypted_key: str, raw_key: bytes,
	query: str
) -> List[dict]:
	"""Query the vault with a search term (username or title needs to contain or match query for entry to match)

	Args:
		hash_encrypted_key (str): The hash of the encrypted key of the user
		raw_key (bytes): The decrypted key of the user
		query (str): The term to search for

	Returns:
		list: The id, title and username of every matching password entry
	"""
	result = list_passwords(hash_encrypted_key, raw_key)
	del raw_key
	query = query.lower()
	filtered_items = []
	for i in result:
		for e in (i['title'], i['username']):
			if query in e.lower():
				filtered_items.append(i)
				break

	return filtered_items

def check_password_popularity(password: str) -> None:
	"""Check if a password is "bad". By default, this would mean it is in the 1 million most used passwords list

	Args:
		password (str): The password to check

	Raises:
		BadPassword: The password is found in the list and thus considered "bad"

	Returns:
		None: The password is not found in the list and thus passes the check
	"""
	path_to_file = join(dirname(__file__), 'lists', 'million_most_used_passwords.txt')
	most_used_passwords = open(path_to_file, 'r').read().split('\n')

	if password in most_used_passwords:
		place_in_list = str(f'{most_used_passwords.index(password) + 1:_}').replace('_','.')
		raise BadPassword(f'Password is at place {place_in_list} of 1.000.000 in the list of most used passwords')

	return

def check_password_pwned(password: str) -> None:
	"""Check if a password is pwned

	Args:
		password (str): The password to check

	Raises:
		BadPassword: The password is has been pwned
	
	Returns:
		None: The password has not been pwned and thus passes the check
	"""	
	hash = sha1(password.encode('utf-8')).hexdigest().upper()
	count = int(dict(map(lambda e: e.split(':'), request.urlopen(f'https://api.pwnedpasswords.com/range/{hash[:5]}').read().decode().split('\r\n'))).get(hash[5:], 0))
	if count > 0:
		raise BadPassword(f'Password has been seen {str(f"{count:_}").replace("_",".")} times before in database leaks')

	return

