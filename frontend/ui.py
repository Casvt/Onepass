#-*- coding: utf-8 -*-

from flask import Blueprint, render_template

ui = Blueprint('ui', __name__)

methods = ['GET']

@ui.route('/', methods=methods)
def ui_login():
	return render_template('login.html')

@ui.route('/vault', methods=methods)
def ui_vault():
	return render_template('vault.html')
