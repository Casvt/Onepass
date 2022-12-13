#-*- coding: utf-8 -*-

from base64 import urlsafe_b64encode
from hashlib import pbkdf2_hmac
from secrets import token_bytes
from typing import Tuple, Union

from cryptography.fernet import Fernet

class Crypt:
	def __init__(self, key: bytes):
		self.cipher = Fernet(key)

	def decode_data(
		self, data: bytes, decode: bool
	) -> Union[bytes, str]:
		"""Decode the passed data if desired otherwise don't touch it

		Args:
			data (bytes): The data to decode
			decode (bool): Wether or not the data should be decoded

		Returns:
			Union[bytes, str]: The decoded data
		"""		
		if decode:
			return data.decode()
		return data

	def decrypt(
		self,
		encrypted_data: Union[bytes, dict, None],
		decode: bool=True
	) -> Union[bytes, str, None]:
		"""Decrypt data

		Args:
			encrypted_data (Union[bytes, dict, None]): The data to decrypt
			decode (bool, optional): Wether or not the resulting data should be decoded. Defaults to True.

		Returns:
			Union[bytes, str, None]: The decrypted data
		"""		
		if encrypted_data is None:
			return

		if isinstance(encrypted_data, bytes):
			#bytes
			result = self.cipher.decrypt(encrypted_data)
			if decode == True:
				result = result.decode()
			return result

		#dict
		for k,v in encrypted_data.items():
			if isinstance(v, bytes):
				encrypted_data[k] = self.decode_data(
					self.cipher.decrypt(v),
					decode
				)

		return encrypted_data

	def encrypt(
		self,
		data: Union[bytes, str, dict, None]
	) -> Union[bytes, None]:
		"""Encrypt data

		Args:
			data (Union[bytes, str, dict, None]): The data to encrypt

		Returns:
			Union[bytes, None]: The encrypted data
		"""		
		if data is None:
			return

		if isinstance(data, dict):
			#dict
			for k, v in data.items():
				if isinstance(v, str):
					v = v.encode()
				if isinstance(v, bytes):
					data[k] = self.cipher.encrypt(v)
			return data

		#str
		if isinstance(data, str):
			data = data.encode()

		#bytes/(str->bytes)
		result = self.cipher.encrypt(data)
		return result

def get_hash(salt: bytes, data: str) -> bytes:
	"""Hash a string using the supplied salt

	Args:
		salt (bytes): The salt to use wwhen hashing
		data (str): The data to hash

	Returns:
		bytes: The b64 encoded hash of the supplied password
	"""
	return urlsafe_b64encode(
		pbkdf2_hmac('sha256', data.encode(), salt, 100_000)
	)

def generate_key(password: str) -> Tuple[bytes, bytes]:
	"""Generate a salt and encrypted key based on a given master password

	Args:
		password (str): The master password to generate for

	Returns:
		Tuple[bytes, bytes]: The salt (1) and encrypted key (2)
	"""
	#hash the master password
	salt = token_bytes()
	hashed_password = get_hash(salt, password)
	del password

	#encrypt key with hashed master password as cipher
	key = Fernet.generate_key()
	encrypted_key = Crypt(hashed_password).encrypt(key)

	return salt, encrypted_key
