#-*- coding: utf-8 -*-

from base64 import urlsafe_b64encode
from secrets import token_bytes
from cryptography.fernet import Fernet, InvalidToken
from hashlib import pbkdf2_hmac
from typing import Tuple

from backend.custom_exceptions import PasswordInvalid

def hash_password(salt: bytes, password: bytes) -> bytes:
	return urlsafe_b64encode(pbkdf2_hmac('sha256', password, salt, 100_000))

def generate_key(password: str) -> Tuple[bytes, bytes, str]:
	"""1. Receives master password.
	
	2. Hashes master password with a generated salt.
	
	3. Encrypts cipher for user passwords with hashed master password
	
	4. Generates hash of encrypted cipher with hash of master password as salt

	Args:
		password (str): The master password of the user

	Returns:
		tuple: Contains three elements. First is salt that master password was hashed with. Second is the cipher used for unlocking user passwords, in encrypted form. Third is the hash of the encrypted cipher.
	"""
	#hash the master password
	salt = token_bytes()
	hashed_password = hash_password(salt, password.encode('utf-8'))
	del password

	#encrypt key with hashed master password as cipher
	encrypted_key = encrypt(key=hashed_password, data=Fernet.generate_key())
	
	#hash encrypted key
	hash_encrypted_key = hash_password(hashed_password, encrypted_key).decode()

	return salt, encrypted_key, hash_encrypted_key

def check_password(salt: bytes, password: bytes, key: bytes) -> Tuple[str, bytes]:
	"""Check if password is correct

	Args:
		salt (bytes): The salt that the master password is hashed with (found in users table)
		password (bytes): The password to check for
		key (bytes): The cipher that will be tried to be decrypted with the password

	Raises:
		PasswordInvalid: The password is not correct

	Returns:
		tuple: First is hash of encrypted key of user. Second is raw key of user. Password is correct
	"""
	#hash password
	hashed_password = hash_password(salt, password.encode('utf-8'))

	#try to decrypt key with hashed password
	try:
		#check if password is correct
		raw_key = decrypt(hashed_password, key)
		#return hash of encrypted key
		return hash_password(hashed_password, key).decode(), raw_key
	except InvalidToken:
		pass
	raise PasswordInvalid

def encrypt(key: bytes, data: bytes) -> bytes:
	"""Encrypt user data with the key of a user

	Args:
		key (bytes): The raw key of the user
		data (bytes): The data to encrypt

	Returns:
		bytes: The encrypted data
	"""	
	cipher = Fernet(key)
	del key
	return cipher.encrypt(data)

def decrypt(key: bytes, encrypted_data: bytes) -> bytes:
	"""Decrypt user data with the key of a user

	Args:
		key (bytes): The raw key of the user
		encrypted_data (bytes): The data to decrypt

	Returns:
		bytes: The decrypted data
	"""	
	cipher = Fernet(key)
	del key
	return cipher.decrypt(encrypted_data)