#-*- coding: utf-8 -*-

class UsernameTaken(Exception):
	"""The username is already taken"""
	api_response = {'error': 'UsernameTaken', 'result': {}, 'code': 400}

class UsernameInvalid(Exception):
	"""The username contains invalid characters"""
	api_response = {'error': 'UsernameInvalid', 'result': {}, 'code': 400}

class UserNotFound(Exception):
	"""The user requested by id or username can not be found"""
	api_response = {'error': 'UserNotFound', 'result': {}, 'code': 404}

class AccessUnauthorized(Exception):
	"""The password given is not correct"""
	api_response = {'error': 'AccessUnauthorized', 'result': {}, 'code': 401}

class PasswordNotFound(Exception):
	"""The password in the vault with the id can not be found"""
	api_response = {'error': 'PasswordNotFound', 'result': {}, 'code': 404}

class KeyNotFound(Exception):
	"""A key was not found in the input that is required to be given"""	
	def __init__(self, key: str=''):
		self.key = key
		super().__init__(self.key)

	@property
	def api_response(self):
		return {'error': 'KeyNotFound', 'result': {'key': self.key}, 'code': 400}
