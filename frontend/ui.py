#-*- coding: utf-8 -*-

from flask import Blueprint, render_template

ui = Blueprint('ui', __name__)

methods = ('GET',)

@ui.route('/not-found', methods=methods)
def ui_not_found():
	return render_template('page_not_found.html')

#===================
# User endpoints
#===================

@ui.route('/', methods=methods)
def ui_login():
	return render_template('login.html')

@ui.route('/create', methods=methods)
def ui_create():
	return render_template('create.html')
	
@ui.route('/settings', methods=methods)
def ui_settings():
	return render_template('settings.html')

#===================
# Password endpoints (vault endpoints)
#===================

@ui.route('/vault', methods=methods)
def ui_vault():
	return render_template('vault.html')

@ui.route('/vault/<id>', methods=methods)
def ui_view_password(id: int):
	return render_template('view_password.html')

@ui.route('/vault/add-password', methods=methods)
def ui_add_password():
	return render_template('add_password.html')
		
@ui.route('/check-password', methods=methods)
def ui_check_password():
	return render_template('check_password.html')
