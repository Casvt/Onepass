#-*- coding: utf-8 -*-

from backend.users import access_user, delete_user, register_user, edit_user_password
from backend.passwords import list_passwords, add_password, search_passwords, get_password, edit_password, delete_password, check_password_popularity, check_password_pwned
from backend.security import encrypt
from backend.custom_exceptions import *

from flask import Blueprint, request, g
from hashlib import sha1
from os import urandom
from time import time

api = Blueprint('api', __name__)
api_key_map = {}

#===================
# Authentication endpoints
#===================

"""
AUTHENTICATION:
	After making a POST /auth/login request, you'll receive an api_key in the output.
	From then on, make all requests with the url parameter api_key, where the value is the string you received.
	One hour after logging in, the api key expires and you are required to login again to get a new api_key.

	If no api key is supplied or it is invalid, 401 'ApiKeyInvalid' is returned.
	If the api key supplied has expired, 401 'ApiKeyExpired' is returned.
"""

def auth(method):
	"""Used as decorator and, if applied to route, restricts the route to authorized users and supplies user specific info
	"""
	def wrapper(*args,**kwargs):
		global api_key_map
		api_key = sha1(request.values.get('api_key','').encode()).hexdigest()
		if api_key_map.get(api_key, {}).get('exp', 0) > time():
			g.raw_api_key = request.values.get('api_key','')
			g.api_key = api_key
			g.user_info = api_key_map[api_key]
			return method(*args, **kwargs)
		else:
			if not api_key in api_key_map:
				#api key not registered
				return {'error': 'ApiKeyInvalid', 'result': {}}, 401
			else:
				#api key expired
				del api_key_map[api_key]
				return {'error': 'ApiKeyExpired', 'result': {}}, 401
	wrapper.__name__ = method.__name__
	return wrapper

@api.route('/auth/login', methods=['POST'])
def api_login():
	"""
	Endpoint: /auth/login
	Description: Login to a user account
	Requires being logged in: No
	Methods:
		POST:
			Parameters (url):
				username (required): the username of the user account
				password (required): the password of the user account
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
	global api_key_map
	data = request.values.to_dict()

	#check if required keys are given
	for required_key in ('username','password'):
		if not required_key in data:
			return {'error': 'KeyNotFound', 'result': {'key': required_key}}, 400

	#check credentials
	try:
		raw_key, user_id, salt = access_user(data['username'], data['password'])
	except UsernameNotFound:
		return {'error': 'UsernameNotFound', 'result': {}}, 404
	except PasswordInvalid:
		return {'error': 'PasswordInvalid', 'result': {}}, 401
	else:
		#login valid
		while 1:
			api_key = sha1(urandom(32)).hexdigest()[:32]
			hashed_api_key = sha1(api_key.encode()).hexdigest()
			if not hashed_api_key in api_key_map:
				break
		encrypted_raw_key = encrypt(api_key.encode(), raw_key, encode=True)
		del raw_key
		exp = time() + 3600
		api_key_map[hashed_api_key] = {'key': encrypted_raw_key, 'salt': salt, 'user_id': user_id, 'exp': exp}
		return {'error': None, 'result': {'api_key': api_key, 'expires': exp}}, 200

@api.route('/auth/logout', methods=['POST'])
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
	global api_key_map
	del api_key_map[g.api_key]
	return {'error': None, 'result': {}}, 200

@api.route('/auth/status', methods=['GET'])
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
					The id of the user account and the expiration time of the api key (epoch)
	"""
	exp = api_key_map[g.api_key]['exp']
	user_id = api_key_map[g.api_key]['user_id']
	return {'error': None, 'result': {'expires': exp, 'user_id': user_id}}, 200

#===================
# User endpoints
#===================

@api.route('/user/add', methods=['POST'])
def api_add_user():
	"""
	Endpoint: /user/add
	Description: Create a new user account
	Requires being logged in: No
	Methods:
		POST:
			Parameters (url):
				username (required): the username of the new user account
				password (required): the password of the new user account
			Returns:
				201:
					The user id of the new user account
				400:
					KeyNotFound: One of the required parameters was not given
					UsernameInvalid: The username given is not allowed
					UsernameTaken: The username given is already in use
	"""
	data = request.values

	#check if required keys are given
	for required_key in ('username','password'):
		if not required_key in data:
			return {'error': 'KeyNotFound', 'result': {'key': required_key}}, 400
	
	#add user
	try:
		user_id = register_user(data['username'], data['password'])
	except UsernameInvalid:
		return {'error': 'UsernameInvalid', 'result': {}}, 400
	except UsernameTaken:
		return {'error': 'UsernameTaken', 'result': {}}, 400
	else:
		return {'error': None, 'result': {'user_id': user_id}}, 201
		
@api.route('/user', methods=['GET','PUT','DELETE'])
@auth
def api_manage_user():
	"""
	Endpoint: /user
	Description: Manage a user account
	Requires being logged in: Yes
	Methods:
		GET:
			Returns:
				200:
					The user id of the user account
		PUT:
			Description: Change the master password of the user account
			Parameters (url):
				old_password (required): the current password of the user account
				new_password (required): the new password of the user account
			Returns:
				200:
					Password updated successfully
				400:
					KeyNotFound: One of the required parameters was not given
					PasswordInvalid: The current password is incorrect
		DELETE:
			Description: Delete the user account
			Returns:
				200:
					Account deleted successfully
	"""
	if request.method == 'GET':
		return {'error': None, 'result': {'user_id': g.user_info['user_id']}}, 200

	elif request.method == 'PUT':
		data = request.values
		
		#check if required key is given
		for required_key in ('old_password','new_password'):
			if not required_key in data:
				return {'error': 'KeyNotFound', 'result': {'key': required_key}}, 400
		
		#edit user
		try:
			edit_user_password(data['old_password'], data['new_password'])
		except PasswordInvalid:
			return {'error': 'PasswordInvalid', 'result': {}}, 400
		else:
			return {'error': None, 'result': {}}, 200
	
	elif request.method == 'DELETE':
		#delete user
		global api_key_map
		delete_user()
		del api_key_map[g.api_key]
		return {'error': None, 'result': {}}, 200

#===================
# Password endpoints (vault endpoints)
#===================

@api.route('/vault', methods=['GET','POST'])
@auth
def api_vault_list():
	"""
	Endpoint: /vault
	Description: Manage the vault
	Requires being logged in: Yes
	Methods:
		GET:
			Description: Get the contents of the vault
			Returns:
				200:
					The id, title and username of every password in the vault
		POST:
			Description: Add a password to the vault
			Parameters (url):
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
		result = list_passwords()
		return {'error': None, 'result': result}, 200
	
	elif request.method == 'POST':
		data = request.values.to_dict()
		if not 'title' in data:
			return {'error': 'KeyNotFound', 'result': {'key': 'title'}}, 400

		result = add_password(title=data['title'],
								url=data.get('url'),
								username=data.get('username'),
								password=data.get('password'))
		return {'error': None, 'result': {'id': result}}, 201

@api.route('/vault/search', methods=['GET'])
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
	if query == None:
		return {'error': 'KeyNotFound', 'result': {'key': 'query'}}, 400

	result = search_passwords(query)
	return {'error': None, 'result': result}, 200
	
@api.route('/vault/<pw_id>', methods=['GET','PUT','DELETE'])
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
					IdNotFound: No password entry found in the vault with the given id
		PUT:
			Description: Edit the password entry
			Parameters (url):
				title: the new title of the password entry
				url: the new url of the password entry
				username: the new username of the password entry
				password: the new password of the password entry
			Returns:
				200:
					Password updated successfully
				404:
					IdNotFound: No password entry found in the vault with the given id
		DELETE:
			Description: Delete the password entry
			Returns:
				200:
					Password entry deleted successfully
				404:
					IdNotFound: No password entry found in the vault with the given id
	"""
	if request.method == 'GET':
		try:
			result = get_password(pw_id)
		except IdNotFound:
			return {'error': 'IdNotFound', 'result': {}}, 404
		else:
			return {'error': None, 'result': result}, 200
			
	elif request.method == 'PUT':
		data = request.values
		try:
			result = edit_password(pw_id,
									title=data.get('title'),
									url=data.get('url'),
									username=data.get('username'),
									password=data.get('password'))
		except IdNotFound:
			return {'error': 'IdNotFound', 'result': {}}, 404
		else:
			return {'error': None, 'result': result}, 200
			
	elif request.method == 'DELETE':
		try:
			delete_password(pw_id)
		except IdNotFound:
			return {'error': 'IdNotFound', 'result': {}}, 404
		else:
			return {'error': None, 'result': {}}, 200

@api.route('/vault/check', methods=['GET'])
@auth
def api_check_password():
	"""
	Endpoint: /vault/check
	Description: Check how good a password is
	Requires being logged in: Yes
	Methods:
		GET:
			Parameters (url):
				password (required): the password to check
			Returns:
				200:
					The results are in on the password
				400:
					KeyNotFound: One of the required parameters was not given
	"""
	data = request.values
	if not 'password' in data:
		return {'error': 'KeyNotFound', 'result': {'key': 'password'}}, 400

	try:
		password = data['password']
		check_password_popularity(password)
		check_password_pwned(password)
	except BadPassword as e:
		return {'error': None, 'result': {'message': str(e)}}, 200
	else:
		return {'error': None, 'result': {'message': 'No problems found with password!'}}, 200
