#-*- coding: utf-8 -*-

class UsernameTaken(Exception):
	"""The username is already taken"""
	pass

class UsernameInvalid(Exception):
	"""The username contains invalid characters"""
	pass

class UsernameNotFound(Exception):
	"""The username requested can not be found"""
	pass

class PasswordInvalid(Exception):
	"""The password given is not correct"""
	pass

class IdNotFound(Exception):
	"""The password in the vault with the id can not be found"""
	pass

class BadPassword(Exception):
	"""The password is considered bad. By default, this means it is in the 1 million most used passwords list"""
	pass