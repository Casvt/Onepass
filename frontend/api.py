#-*- coding: utf-8 -*-

from os import urandom
from time import time
from typing import Any, Tuple, Union

from flask import Blueprint, g, request

from backend.custom_exceptions import (AccessUnauthorized, KeyNotFound,
                                       PasswordNotFound, UsernameInvalid,
                                       UsernameTaken, UserNotFound)
from backend.users import User, register_user

api = Blueprint('api', __name__)
api_key_map = {}

"""
AUTHENTICATION:
	After making a POST /auth/login request, you'll receive an api_key in the output.
	From then on, make all requests with the url parameter api_key, where the value is the string you received.
	One hour after logging in, the api key expires and you are required to login again to get a new api_key.

	If no api key is supplied or it is invalid, 401 'ApiKeyInvalid' is returned.
	If the api key supplied has expired, 401 'ApiKeyExpired' is returned.
"""

def return_api(result: Any, error: str=None, code: int=200) -> Tuple[dict, int]:
	return {'error': error, 'result': result}, code

def auth(method):
	"""Used as decorator and, if applied to route, restricts the route to authorized users and supplies user specific info
	"""
	def wrapper(*args,**kwargs):
		hashed_api_key = hash(request.values.get('api_key',''))
		if not hashed_api_key in api_key_map:
			return return_api({}, 'ApiKeyInvalid', 401)
		
		exp = api_key_map[hashed_api_key]['exp']
		if exp <= time():
			return return_api({}, 'ApiKeyExpired', 401)
		
		# Api key valid
		g.hashed_api_key = hashed_api_key
		g.exp = exp
		g.user_data = api_key_map[hashed_api_key]['user_data']
		return method(*args, **kwargs)

	wrapper.__name__ = method.__name__
	return wrapper

def error_handler(method):
	"""Catches the errors that can occur in the endpoint and returns the correct api error
	"""
	def wrapper(*args, **kwargs):
		try:
			return method(*args, **kwargs)
		except (UsernameTaken, UsernameInvalid, UserNotFound,
				AccessUnauthorized, PasswordNotFound, KeyNotFound) as e:
			return return_api(**e.api_response)

	wrapper.__name__ = method.__name__
	return wrapper

def check_keys(data: Union[dict, str, None], keys: Tuple[str,...]) -> None:
	if isinstance(data, dict):
		for key in keys:
			if not key in data:
				raise KeyNotFound(key)
	else:
		if data is None:
			raise KeyNotFound(keys[0])
	return

#===================
# Authentication endpoints
#===================

@api.route('/auth/login', methods=['POST'])
@error_handler
def api_login():
	"""
	Endpoint: /auth/login
	Description: Login to a user account
	Requires being logged in: No
	Methods:
		POST:
			Parameters (body (content-type: application/json)):
				username (required): the username of the user account
				master_password (required): the password of the user account
			Returns:
				200:
					The apikey to use for further requests and expiration time (epoch)
				400:
					KeyNotFound: One of the required parameters was not given
				401:
					PasswordInvalid: The password given is not correct for the user account
				404:
					UsernameNotFound: The username was not found
	"""
	data = request.get_json()

	#check if required keys are given
	check_keys(data, ('username', 'master_password'))

	#check credentials
	user = User(data['username'], data['master_password'])

	#login valid
	while 1:
		api_key = urandom(16).hex() # <- length api key / 2
		hashed_api_key = hash(api_key)
		if not hashed_api_key in api_key_map:
			break
	exp = time() + 3600
	api_key_map.update({
		hashed_api_key: {
			'exp': exp,
			'user_data': user
		}
	})

	result = {'api_key': api_key, 'expires': exp}
	return return_api(result)

@api.route('/auth/logout', methods=['POST'])
@error_handler
@auth
def api_logout():
	"""
	Endpoint: /auth/logout
	Description: Logout of a user account
	Requires being logged in: Yes
	Methods:
		POST:
			Returns:
				200:
					Logout successful
	"""
	api_key_map.pop(g.hashed_api_key)
	return return_api({})

@api.route('/auth/status', methods=['GET'])
@error_handler
@auth
def api_status():
	"""
	Endpoint: /auth/status
	Description: Get current status of login
	Requires being logged in: Yes
	Methods:
		GET:
			Returns:
				200:
					The username of the logged in account and the expiration time of the api key (epoch)
	"""
	result = {
		'expires': api_key_map[g.hashed_api_key]['exp'],
		'username': api_key_map[g.hashed_api_key]['user_data'].username
	}
	return return_api(result)

#===================
# User endpoints
#===================

@api.route('/user/add', methods=['POST'])
@error_handler
def api_add_user():
	"""
	Endpoint: /user/add
	Description: Create a new user account
	Requires being logged in: No
	Methods:
		POST:
			Parameters (body (content-type: application/json)):
				username (required): the username of the new user account
				master_password (required): the password of the new user account
			Returns:
				201:
					The user id of the new user account
				400:
					KeyNotFound: One of the required parameters was not given
					UsernameInvalid: The username given is not allowed
					UsernameTaken: The username given is already in use
	"""
	data = request.get_json()

	#check if required keys are given
	check_keys(data, ('username', 'master_password'))
	
	#add user
	user_id = register_user(data['username'], data['master_password'])
	return return_api({'user_id': user_id}, code=201)
		
@api.route('/user', methods=['PUT','DELETE'])
@error_handler
@auth
def api_manage_user():
	"""
	Endpoint: /user
	Description: Manage a user account
	Requires being logged in: Yes
	Methods:
		PUT:
			Description: Change the master password of the user account
			Parameters (body (content-type: application/json)):
				new_master_password (required): the new password of the user account
			Returns:
				200:
					Password updated successfully
				400:
					KeyNotFound: One of the required parameters was not given
		DELETE:
			Description: Delete the user account
			Returns:
				200:
					Account deleted successfully
	"""
	if request.method == 'PUT':
		data = request.get_json()
		
		#check if required key is given
		check_keys(data, ('new_master_password',))
		
		#edit user
		g.user_data.edit_master_password(data['new_master_password'])
		return return_api({})
	
	elif request.method == 'DELETE':
		#delete user
		g.user_data.delete()
		api_key_map.pop(g.hashed_api_key)
		return return_api({})

#===================
# Vault endpoints
#===================

@api.route('/vault', methods=['GET','POST'])
@error_handler
@auth
def api_vault_list():
	"""
	Endpoint: /vault
	Description: Manage the vault
	Requires being logged in: Yes
	Methods:
		GET:
			Description: Get the contents of the vault
			Parameters (url):
				sort_by: how to sort the result. Allowed values are 'title', 'title_reversed', 'date_added' and 'date_added_reversed'
			Returns:
				200:
					The id, title, url and username of every password in the vault
		POST:
			Description: Add a password to the vault
			Parameters (body (content-type: application/json)):
				title (required): the title of the password entry
				url: the url of the site that the password is for
				username: the username of the account
				password: the password of the account
			Returns:
				200:
					The id of the new password entry
				400:
					KeyNotFound: One of the required parameters was not given
	"""
	if request.method == 'GET':
		sort_by = request.values.get('sort_by','title')
		result = g.user_data.vault.fetchall(sort_by=sort_by)
		return return_api(result)
	
	elif request.method == 'POST':
		data = request.get_json()
		check_keys(data, ('title',))

		result = g.user_data.vault.add(title=data['title'],
								url=data.get('url'),
								username=data.get('username'),
								password=data.get('password'))
		return return_api(result.get(), code=201)

@api.route('/vault/search', methods=['GET'])
@error_handler
@auth
def api_vault_query():
	"""
	Endpoint: /vault/search
	Description: Search through the vault
	Requires being logged in: Yes
	Methods:
		GET:
			Parameters (url):
				query (required): The search term
			Returns:
				200:
					The search results, listed like GET /vault
				400:
					KeyNotFound: One of the required parameters was not given
	"""
	query = request.values.get('query')
	check_keys(query, ('query',))

	result = g.user_data.vault.search(query)
	return return_api(result)

@api.route('/vault/<pw_id>', methods=['GET','PUT','DELETE'])
@error_handler
@auth
def api_get_password(pw_id: int):
	"""
	Endpoint: /vault/<pw_id>
	Description: Manage a specific password entry in the vault
	Requires being logged in: Yes
	URL Parameters:
		<pw_id>:
			The id of the password entry
	Methods:
		GET:
			Returns:
				200:
					All info about the password entry
				404:
					No password entry found in the vault with the given id
		PUT:
			Description: Edit the password entry
			Parameters (body (content-type: application/json)):
				title: the new title of the password entry
				url: the new url of the password entry
				username: the new username of the password entry
				password: the new password of the password entry
			Returns:
				200:
					Password updated successfully
				404:
					No password entry found in the vault with the given id
		DELETE:
			Description: Delete the password entry
			Returns:
				200:
					Password entry deleted successfully
				404:
					No password entry found in the vault with the given id
	"""
	if request.method == 'GET':
		result = g.user_data.vault.fetchone(pw_id)
		return return_api(result.get())
			
	elif request.method == 'PUT':
		data = request.get_json()
		result = g.user_data.vault.fetchone(pw_id).update(title=data.get('title'),
														url=data.get('url'),
														username=data.get('username'),
														password=data.get('password'))
		return return_api(result)
			
	elif request.method == 'DELETE':
		g.user_data.vault.fetchone(pw_id).delete()
		return return_api({})

@api.route('/vault/<pw_id>/check', methods=['GET'])
@error_handler
@auth
def api_check_password(pw_id: int):
	"""
	Endpoint: /vault/<pw_id>/check
	Description: Check how good a password is
	Requires being logged in: Yes
	URL Parameters:
		<pw_id>:
			The id of the password entry
	Methods:
		GET:
			Returns:
				200:
					The results are in on the password
				404:
					No password entry found in the vault with the given id
	"""
	result = g.user_data.vault.fetchone(pw_id).check()
	return return_api(result)
