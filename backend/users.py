#-*- coding: utf-8 -*-

from typing import Tuple
from flask import g

from backend.custom_exceptions import *
from backend.security import generate_key, get_key, check_password, hash_password, encrypt
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
	if username in ONEPASS_INVALID_USERNAMES or username.isdigit():
		raise UsernameInvalid
	if filter(lambda c: not c in ONEPASS_USERNAME_CHARACTERS, username):
		raise UsernameInvalid

	#check if username isn't already taken
	cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
	if cursor.fetchone() != None:
		raise UsernameTaken

	#generate salt and key exclusive for user
	salt, encrypted_key, hash_key = generate_key(password=password)
	del password

	#add user to userlist and create it's "vault"
	cursor.execute("""
		INSERT INTO users(username, salt, key)
		VALUES (?,?,?);
	""", (username, salt, encrypted_key))
	del username
	user_id = cursor.lastrowid
	cursor.execute(f"""
		CREATE TABLE `{hash_key}` (
			id INTEGER PRIMARY KEY,
			title VARCHAR(254),
			url TEXT,
			username TEXT,
			password TEXT
		)
	""")

	return user_id

def access_user(user: str, password: str) -> Tuple[bytes, int, bytes]:
	"""Get access to a user accounts info

	Args:
		user (str): The username of the user account
		password (str): The master password of the user account

	Raises:
		UsernameNotFound: The username is not found
		PasswordInvalid: The master password is not correct

	Returns:
		Tuple[bytes, int, bytes]: The raw key (1), user id (2) and salt (3) of the user account
	"""
	cursor = get_db(output_type='dict')

	#check if user exists
	if user.isdigit():
		cursor.execute("SELECT * FROM users WHERE id = ?", (user,))
	else:
		cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
	del user
	result = cursor.fetchone()
	if result == None:
		raise UsernameNotFound

	#check if password is correct
	return check_password(salt=result['salt'], password=password, key=result['key']), result['id'], result['salt']

def edit_user_password(old_password: str, new_password: str) -> None:
	"""Edit the master password of the user

	Args:
		old_password (str): The current master password
		new_password (str): The new master password

	Raises:
		PasswordInvalid: The master password (old_password) is not correct

	Returns:
		None: password successfully changed
	"""
	raw_key, user_id, salt = access_user(str(g.user_info['user_id']), old_password)
	cursor = get_db()

	#encrypt raw key with new password
	new_hashed_password = hash_password(salt, new_password.encode())
	del new_password
	new_encrypted_key = encrypt(new_hashed_password, raw_key)

	#insert new encrypted key
	cursor.execute("UPDATE users SET key = ? WHERE id = ?;", (new_encrypted_key, user_id))

	return

def delete_user() -> None:
	"""Delete a user

	Returns:
		None: user successfully deleted
	"""
	cursor = get_db()

	#get hash of encrypted key of user
	hash_key = get_key()[1]

	#delete in database
	cursor.execute("DELETE FROM users WHERE id = ?;", (g.user_info['user_id'],))
	cursor.execute(f"DROP TABLE IF EXISTS `{hash_key}`;")

	return
