#-*- coding: utf-8 -*-

from base64 import urlsafe_b64encode
from secrets import token_bytes
from cryptography.fernet import Fernet, InvalidToken
from hashlib import pbkdf2_hmac
from typing import Tuple
from flask import g

from backend.custom_exceptions import PasswordInvalid

def hash_password(salt: bytes, password: bytes) -> bytes:
	"""Hash a string using the supplied salt

	Args:
		salt (bytes): The salt to use wwhen hashing
		password (bytes): The password to hash

	Returns:
		bytes: The urlsafe_b64encode'ed hash of the supplied password
	"""
	return urlsafe_b64encode(pbkdf2_hmac('sha256', password, salt, 100_000))

def generate_key(password: str) -> Tuple[bytes, bytes, str]:
	"""Generate a salt, encrypted key and the hash of the key based on a given master password

	Args:
		password (str): The master password to generate for

	Returns:
		Tuple[bytes, bytes, str]: The salt (1), encrypted key (2) and hash of key (3)
	"""
	#hash the master password
	salt = token_bytes()
	hashed_password = hash_password(salt, password.encode('utf-8'))
	del password

	#encrypt key with hashed master password as cipher
	key = Fernet.generate_key()
	encrypted_key = encrypt(key=hashed_password, data=key)

	#hash key
	hash_key = hash_password(salt, key).decode()

	return salt, encrypted_key, hash_key

def get_key() -> Tuple[bytes, str]:
	"""Extract the raw key and hash of key from the request variables (flasks 'g')

	Returns:
		Tuple[bytes, str]: The raw key (1) and hash of key (2)
	"""
	raw_key = decrypt(g.raw_api_key.encode(), g.user_info['key'], encode=True)
	hash_key = hash_password(g.user_info['salt'], raw_key).decode()
	return raw_key, hash_key

def check_password(salt: bytes, password: bytes, key: bytes) -> bytes:
	"""Check if password is correct

	Args:
		salt (bytes): The salt that the master password is hashed with (found in users table)
		password (bytes): The password to check for
		key (bytes): The cipher that will be tried to be decrypted with the password

	Raises:
		PasswordInvalid: The password is not correct

	Returns:
		bytes: The raw key of the user account
	"""
	#hash password
	hashed_password = hash_password(salt, password.encode('utf-8'))

	#try to decrypt key with hashed password
	try:
		#check if password is correct
		raw_key = decrypt(hashed_password, key)
		#return hash of encrypted key
		return raw_key
	except InvalidToken:
		pass
	raise PasswordInvalid

def encrypt(key: bytes, data: bytes, encode=False) -> bytes:
	"""Encrypt user data with the raw key of a user

	Args:
		key (bytes): The raw key of the user
		data (bytes): The user data to encrypt
		encode (bool, optional): urlsafe_b64encode the key before using it. Defaults to False.

	Returns:
		bytes: The encrypted data
	"""
	if encode == True:
		cipher = Fernet(urlsafe_b64encode(key))
	else:
		cipher = Fernet(key)
	del key
	return cipher.encrypt(data)

def decrypt(key: bytes, encrypted_data: bytes, encode=False) -> bytes:
	"""Decrypt user data with the raw key of a user

	Args:
		key (bytes): The raw key of the user
		encrypted_data (bytes): The encrypted user data to decrypt
		encode (bool, optional): urlsafe_b64encode the key before using it. Defaults to False.

	Returns:
		bytes: The decrypted data
	"""
	if encode == True:
		cipher = Fernet(urlsafe_b64encode(key))
	else:
		cipher = Fernet(key)
	del key
	return cipher.decrypt(encrypted_data)
