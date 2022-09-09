#-*- coding: utf-8 -*-

from backend.backend import *

from flask import Blueprint, request
from hashlib import sha1
from os import urandom

api = Blueprint('api', __name__)
api_key_map = {}
user_info_map = {}

#===================
# Authentication endpoints
#===================

def auth(method):
	def wrapper(*args,**kwargs):
		if sha1(request.values.to_dict().get('api_key','').encode('utf-8')).hexdigest() in api_key_map.get(request.remote_addr, []):
			return method(*args, **kwargs)
		else:
			return {'error': 'ApiKeyInvalid', 'result': {}}, 401
	wrapper.__name__ = method.__name__
	return wrapper

@api.route('/login', methods=['POST'])
def api_login():
	global api_key_map, user_info_map
	data = request.values.to_dict()

	#check if required keys are given
	for required_key in ('username','password'):
		if not required_key in data:
			return {'error': 'KeyNotFoundInBody', 'result': {'key': required_key}}, 400

	#check credentials
	try:
		hash_encrypted_key, raw_key = access_user(data['username'],data['password'])
	except UsernameNotFound:
		return {'error': 'UsernameNotFound', 'result': {}}, 404
	except PasswordInvalid:
		return {'error': 'PasswordInvalid', 'result': {}}, 401
	else:
		#login valid
		api_key = sha1(urandom(32)).hexdigest()[:32]
		hashed_api_key = sha1(api_key.encode('utf-8')).hexdigest()
		api_key_map[request.remote_addr] = api_key_map.get(request.remote_addr, []) + [hashed_api_key]
		user_info_map[request.remote_addr] = {'hash_encrypted_key': hash_encrypted_key, 'raw_key': raw_key}
		return {'error': None, 'result': {'api_key': api_key}}, 200

@api.route('/logout', methods=['POST'])
@auth
def api_logout():
	global api_key_map, user_info_map
	hashed_api_key = sha1(request.values.to_dict().get('api_key','').encode('utf-8')).hexdigest()
	api_key_map[request.remote_addr].remove(hashed_api_key)
	user_info_map.pop(request.remote_addr)
	return {'error': None, 'result': {}}, 200

#===================
# User endpoints
# These do not require token authentication and instead rely on parsing user data via arguments.
#===================

@api.route('/user/add', methods=['POST'])
def api_add_user():
	data = request.values.to_dict()

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

@api.route('/user/edit', methods=['PUT'])
def api_edit_user():
	data = request.values.to_dict()
	
	#check if required keys are given
	for required_key in ('username','old_password','new_password'):
		if not required_key in data:
			return {'error': 'KeyNotFound', 'result': {'key': required_key}}, 400
	
	#edit user
	try:
		edit_user_password(data['username'], data['old_password'], data['new_password'])
	except UsernameNotFound:
		return {'error': 'UsernameNotFound', 'result': {}}, 404
	except PasswordInvalid:
		return {'error': 'PasswordInvalid', 'result': {}}, 401
	else:
		return {'error': None, 'result': {}}, 200
		
@api.route('/user', methods=['DELETE'])
def api_delete_user():
	data = request.values.to_dict()
	
	#check if required keys are given
	for required_key in ('username','password'):
		if not required_key in data:
			return {'error': 'KeyNotFoundInBody', 'result': {'key': required_key}}, 400

	#delete user
	try:
		delete_user(data['username'], data['password'])
	except UsernameNotFound:
		return {'error': 'UsernameNotFound', 'result': {}}, 404
	except PasswordInvalid:
		return {'error': 'PasswordInvalid', 'result': {}}, 401
	else:
		return {'error': None, 'result': {}}, 200

#===================
# Password endpoints (vault endpoints)
# These require token authentication
#===================

@api.route('/vault', methods=['GET','POST'])
@auth
def api_vault_list():
	if request.method == 'GET':
		result = list_passwords(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'])
		print(result)
		return {'error': None, 'result': result}, 200
	
	elif request.method == 'POST':
		data = request.values.to_dict()
		if not 'title' in data:
			return {'error': 'KeyNotFound', 'result': {'key': 'title'}}, 400

		result = add_password(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'],
								title=data['title'],
								url=data.get('url'),
								username=data.get('username'),
								password=data.get('password'))
		return {'error': None, 'result': {'id': result}}, 201

@api.route('/vault/search', methods=['GET'])
@auth
def api_vault_query():
	query = request.values.to_dict().get('query')
	if query == None:
		return {'error': 'KeyNotFound', 'result': {'key': 'query'}}, 400

	result = search_passwords(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'], query)
	return {'error': None, 'result': result}, 200
	
@api.route('/vault/<pw_id>', methods=['GET','PUT','DELETE'])
@auth
def api_get_password(pw_id: int):
	if request.method == 'GET':
		try:
			result = get_password(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'], pw_id)
		except IdNotFound:
			return {'error': 'IdNotFound', 'result': {}}, 404
		else:
			return {'error': None, 'result': result}, 200
			
	elif request.method == 'PUT':
		data = request.values.to_dict()
		try:
			result = edit_password(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'], pw_id,
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
			delete_password(user_info_map[request.remote_addr]['hash_encrypted_key'], pw_id)
		except IdNotFound:
			return {'error': 'IdNotFound', 'result': {}}, 404
		else:
			return {'error': None, 'result': {}}, 200

@api.route('/vault/<pw_id>/check', methods=['GET'])
@auth
def api_check_password(pw_id: int):
	try:
		password = get_password(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'], pw_id)['password']
		check_password_popularity(password)
		check_password_pwned(password)
	except BadPassword as e:
		return {'error': None, 'result': {'message': str(e)}}, 200
	else:
		return {'error': None, 'result': {'message': 'No problems found with password!'}}, 200
