#-*- coding: utf-8 -*-

from backend.backend import *

from flask import Blueprint, redirect, request, render_template
from os import urandom
from hashlib import sha1

ui = Blueprint('ui', __name__)
api_key_map = {}
user_info_map = {}

def auth(method):
	def wrapper(*args,**kwargs):
		if sha1(request.values.to_dict().get('api_key','').encode('utf-8')).hexdigest() in api_key_map.get(request.remote_addr, []):
			return method(*args, **kwargs)
		else:
			return {'error': 'redirect to login', 'result': {}}, 200
	wrapper.__name__ = method.__name__
	return wrapper

@ui.route('/', methods=['GET', 'POST', 'PUT'])
def ui_login():
	if request.method == 'GET':
		return render_template('login.html')

	elif request.method == 'POST':
		global api_key_map, user_info_map
		data = request.get_json(force=True)
		#check credentials
		try:
			hash_encrypted_key, raw_key = access_user(data['username'], data['password'])
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

	elif request.method == 'PUT':
		token = request.values.to_dict().get('api_key', '')
		if sha1(token.encode('utf-8')).hexdigest() in api_key_map.get(request.remote_addr, []):
			return 'VALID'
		else:
			return 'INVALID'

@ui.route('/not-found', methods=['GET'])
def ui_not_found():
	return render_template('page_not_found.html')

@ui.route('/create', methods=['GET','POST'])
def ui_create():
	if request.method == 'GET':
		return render_template('create.html', error='')
		
	elif request.method == 'POST':
		data = request.form.to_dict()
		
		#add user
		try:
			register_user(data['username'], data['password'])
		except UsernameInvalid:
			return render_template('create.html', error='*Invalid username')
		except UsernameTaken:
			return render_template('create.html', error='*Username already taken')
		else:
			return redirect('/')

@auth
def ui_vault_post(request):
	result = list_passwords(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'])
	return {'error': None, 'result': result}, 200
	
@ui.route('/vault', methods=['GET','POST'])
def ui_vault():
	if request.method == 'GET':
		return render_template('vault.html')
	
	elif request.method == 'POST':
		return ui_vault_post(request)
		
@ui.route('/vault/search', methods=['GET'])
@auth
def ui_search():
	query = request.values.to_dict().get('query')
	result = search_passwords(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'], query)
	return {'error': None, 'result': result}, 200

@auth
def ui_add_password_post(request):
	data = request.values.to_dict()
	result = add_password(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'],
							title=data['title'],
							url=data.get('url'),
							username=data.get('username'),
							password=data.get('password'))
	return redirect(f'/vault/{result}')

@ui.route('/vault/add-password', methods=['GET','POST'])
def ui_add_password():
	if request.method == 'GET':
		return render_template('add_password.html')

	elif request.method == 'POST':
		return ui_add_password_post(request)
		
@auth
def ui_edit_password(request, id: int):
	data = request.values.to_dict()
	try:
		edit_password(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'], id,
						title=data.get('title'),
						url=data.get('url'),
						username=data.get('username'),
						password=data.get('password'))
	except IdNotFound:
		return render_template('page_not_found.html'), 404
	else:
		return render_template('view_password.html'), 200

@auth
def ui_get_password(request, id: int):
	try:
		result = get_password(user_info_map[request.remote_addr]['hash_encrypted_key'], user_info_map[request.remote_addr]['raw_key'], id)
	except IdNotFound:
		return render_template('page_not_found.html'), 404
	else:
		return {'error': None, 'result': result}, 200

@auth
def ui_delete_password(request, id: int):
	try:
		delete_password(user_info_map[request.remote_addr]['hash_encrypted_key'], id)
	except IdNotFound:
		return render_template('page_not_found.html'), 404
	else:
		return {'error': None, 'result': {}}, 200

@ui.route('/vault/<id>', methods=['GET','POST','PUT','DELETE'])
def ui_view_password(id: int):
	if request.method == 'GET':
		return render_template('view_password.html')

	elif request.method == 'PUT':
		return ui_get_password(request, id)
	
	elif request.method == 'POST':
		return ui_edit_password(request, id)

	elif request.method == 'DELETE':
		return ui_delete_password(request, id)
		
@ui.route('/check-password', methods=['GET','POST'])
def ui_check_password():
	if request.method == 'GET':
		return render_template('check_password.html')
	
	elif request.method == 'POST':
		try:
			password = request.get_json(force=True)['password']
			check_password_popularity(password)
			check_password_pwned(password)
		except BadPassword as e:
			return {'error': None, 'result': {'message': str(e)}}, 200
		else:
			return {'error': None, 'result': {'message': 'No problems found with password!'}}, 200

@ui.route('/settings', methods=['GET','POST','DELETE'])
def ui_settings():
	if request.method == 'GET':
		return render_template('settings.html')

	elif request.method == 'DELETE':
		try:
			data = request.values.to_dict()
			delete_user(data['username'], data['password'])
		except UsernameNotFound:
			pass
		except PasswordInvalid:
			pass
		else:
			return {'error': None, 'result': {}}, 200

	elif request.method == 'POST':
		try:
			data = request.form.to_dict()
			edit_user_password(data['username'], data['old_password'], data['new_password'])
		except UsernameNotFound:
			pass
		except PasswordInvalid:
			pass
		else:
			return redirect('/')