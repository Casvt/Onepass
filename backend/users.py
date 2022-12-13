#-*- coding: utf-8 -*-

from cryptography.fernet import InvalidToken

from backend.custom_exceptions import (AccessUnauthorized, UsernameInvalid,
                                       UsernameTaken, UserNotFound)
from backend.db import get_db
from backend.passwords import Vault
from backend.security import Crypt, generate_key, get_hash

ONEPASS_USERNAME_CHARACTERS = 'abcedfghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.!@$'
ONEPASS_INVALID_USERNAMES = ['users','api']

class User:
	"""Represents an user account
	"""	
	def __init__(self, username: str, master_password: str):
		# fetch data of user to check if user exists and to check if password is correct
		result = get_db(dict).execute(
			"SELECT id, salt, encrypted_key FROM users WHERE username = ?", 
			(username,)
		).fetchone()
		if result is None:
			raise UserNotFound
		self.username = username
		self.user_id = result['id']

		# check password
		hash_master_password = get_hash(result['salt'], master_password)
		try:
			self.key = Crypt(hash_master_password).decrypt(
				result['encrypted_key'], decode=False
			)
			self.salt = result['salt']
		except InvalidToken:
			raise AccessUnauthorized
			
	@property
	def vault(self) -> Vault:
		"""Get access to the vault of the user account

		Returns:
			Vault: Vault instance that can be used to access the vault of the user account
		"""		
		if not hasattr(self, 'vault_instance'):
			self.vault_instance = Vault(self.user_id, self.key)
		return self.vault_instance
		
	def edit_master_password(self, new_master_password: str) -> None:
		"""Change the master password of the account

		Args:
			new_master_password (str): The new master password
		"""		
		#encrypt raw key with new password
		hash_master_password = get_hash(self.salt, new_master_password)
		encrypted_key = Crypt(hash_master_password).encrypt(self.key)

		#update database
		get_db().execute(
			"UPDATE users SET encrypted_key = ? WHERE id = ?",
			(encrypted_key, self.user_id)
		)
		return

	def delete(self) -> None:
		"""Delete the user account
		"""		
		cursor = get_db()
		cursor.execute("DELETE FROM users WHERE id = ?", (self.user_id,))
		cursor.execute("DELETE FROM vault WHERE user_id = ?", (self.user_id,))
		return

def _check_username(username: str) -> None:
	"""Check if username is valid

	Args:
		username (str): The username to check

	Raises:
		UsernameInvalid: The username is not valid
	"""	
	if username in ONEPASS_INVALID_USERNAMES or username.isdigit():
		raise UsernameInvalid
	if list(filter(lambda c: not c in ONEPASS_USERNAME_CHARACTERS, username)):
		raise UsernameInvalid
	return

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
	#check if username is valid
	_check_username(username)

	cursor = get_db()

	#check if username isn't already taken
	if cursor.exists("SELECT username FROM users WHERE username = ?", (username,)):
		raise UsernameTaken

	#generate salt and key exclusive for user
	salt, encrypted_key = generate_key(password=password)
	del password

	#add user to userlist
	user_id = cursor.execute(
		"""
		INSERT INTO users(username, salt, encrypted_key)
		VALUES (?,?,?);
		""",
		(username, salt, encrypted_key)
	).lastrowid

	return user_id
