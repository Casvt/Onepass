#-*- coding: utf-8 -*-

from typing import Tuple

from backend.custom_exceptions import *
from backend.security import generate_key, check_password, hash_password, encrypt
from backend.db import get_db

ONEPASS_USERNAME_CHARACTERS = 'abcedfghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.!@$'
ONEPASS_INVALID_USERNAMES = ['users','api']

def register_user(username: str, password: str) -> int:
	"""Add a user

	Args:
		username (str): The username of the new user
		password (str): The master password of the new user

	Raises:
		UsernameInvalid: Username not allowed or contains invalid characters
		UsernameTaken: Username is already taken; usernames must be unique

	Returns:
		user_id (int): The id of the new user. User registered successful
	"""
	cursor = get_db()

	#check if username is valid
	if username in ONEPASS_INVALID_USERNAMES:
		raise UsernameInvalid
	for i in username:
		if not str(i) in ONEPASS_USERNAME_CHARACTERS:
			raise UsernameInvalid(f'The following character is not allowed: {str(i)}')

	#check if username isn't already taken
	cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
	if cursor.fetchone() != None:
		raise UsernameTaken

	#generate salt and key exclusive for user
	salt, encrypted_key, hash_encrypted_key = generate_key(password=password)
	del password

	#add user to userlist and create it's "vault"
	cursor.execute("""
		INSERT INTO users(username, salt, key)
		VALUES (?,?,?);
	""", (username, salt, encrypted_key))
	del username
	user_id = cursor.lastrowid
	cursor.execute(f"""
		CREATE TABLE `{hash_encrypted_key}` (
			id INTEGER PRIMARY KEY,
			title VARCHAR(254),
			url TEXT,
			username TEXT,
			password TEXT
		)
	""")

	return user_id

def access_user(username: str, password: str) -> Tuple[str, bytes]:
	"""Check if login credentials are correct for a user

	Args:
		username (str): The username
		password (str): The master password of the user

	Raises:
		UsernameNotFound: The username is not found
		PasswordInvalid: The master password is incorrect

	Returns:
		tuple: Both elements in str format. First is hash of encrypted key of user. Second is raw key of user.
	"""
	cursor = get_db(output_type='dict')

	#check if user exists
	cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
	del username
	result = cursor.fetchone()
	if result == None:
		raise UsernameNotFound
	result = dict(result)

	#check if password is correct
	try:
		return check_password(salt=result['salt'], password=password, key=result['key'])
	except PasswordInvalid:
		#password is not correct
		pass
	raise PasswordInvalid

def edit_user_password(username: str, old_password: str, new_password: str) -> None:
	"""Edit the master password of the user

	Args:
		username (str): The username of the user to target
		old_password (str): The current master password
		new_password (str): The new master password

	Raises:
		UsernameNotFound: The username is not found
		PasswordInvalid: The old master password is incorrect

	Returns:
		None: password successfully changed
	"""
	cursor = get_db()

	#get hash of encrypted key of user
	hash_encrypted_key, raw_key = access_user(username, old_password)

	#get salt and encrypted key of user
	cursor.execute("SELECT salt FROM users WHERE username = ?;", (username,))
	salt = cursor.fetchone()[0]

	#encrypt raw key with new password
	new_hashed_password = hash_password(salt, new_password.encode('utf-8'))
	del new_password
	new_encrypted_key = encrypt(new_hashed_password, raw_key)

	#insert new encrypted key
	cursor.execute("UPDATE users SET key = ? WHERE username = ?;", (new_encrypted_key, username))
	del username

	#update table name of user
	new_hash_encrypted_key = hash_password(new_hashed_password, new_encrypted_key).decode()
	cursor.execute(f"ALTER TABLE `{hash_encrypted_key}` RENAME TO `{new_hash_encrypted_key}`;")

	return

def delete_user(username: str, password: str) -> None:
	"""Delete a user

	Args:
		username (str): The username of the user to delete
		password (str): The master password of the user

	Raises:
		UsernameNotFound: The username is not found
		PasswordInvalid: The old master password is incorrect

	Returns:
		None: user successfully deleted
	"""

	cursor = get_db()

	#get hash of encrypted key of user
	hash_encrypted_key = access_user(username, password)[0]
	del password

	#delete in database
	cursor.execute("DELETE FROM users WHERE username = ?;", (username,))
	del username
	cursor.execute(f"DROP TABLE IF EXISTS `{hash_encrypted_key}`;")

	return
