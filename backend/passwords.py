# -*- coding: utf-8 -*-

from hashlib import sha1
from typing import List, Literal, Union
from urllib import request

from backend.custom_exceptions import PasswordNotFound
from backend.db import get_db
from backend.security import Crypt

class _CheckPassword:
	"""Check if a password is considered "safe"
	"""	
	def __init__(self, password: str):
		self._checks = [
			self._in_top_million,
			self._pwned
		]
		self.password = password

	def check_password(self) -> dict:
		"""Run all checks on the password

		Returns:
			dict: The result of the checks
		"""		
		for check in self._checks:
			result = check()
			if not result is None:
				return result

		return {"place": -1, "message": "No problems found with the password!"}

	def _in_top_million(self) -> Union[dict, None]:
		"""Check if password is in top 1.000.000 passwords list
		"""
		result = get_db().execute(
			"SELECT rowid FROM most_used_passwords WHERE password = ?",
			(self.password,)
		).fetchone()

		if result is not None:
			place_in_list = f"{result[0]:_}".replace("_", ".")
			return {
				"place": place_in_list,
				"message": f"Password is at place {place_in_list} of 1.000.000 in the list of most used passwords",
			}
		return
		
	def _pwned(self) -> Union[dict, None]:
		"""Check if password has been pwned according to pwnedpasswords.com
		"""
		hash = sha1(self.password.encode()).hexdigest().upper()
		pwned_range = dict(
			map(
				lambda e: e.split(":"),
				request.urlopen(f"https://api.pwnedpasswords.com/range/{hash[:5]}").read().decode().split("\r\n")
			)
		)
		count = int(pwned_range.get(hash[5:], 0))
		if count > 0:
			place_in_list = f"{count:_}".replace("_", ".")
			return {
				"place": place_in_list,
				"message": f"Password has been seen {place_in_list} times before in database leaks",
			}
		return

class Password:
	"""Represents a password in the vault of the user
	"""	
	def __init__(self, password_id: int, key: bytes):
		self.id = password_id
		self.key = key

		# check if pw exists
		if not get_db().exists("SELECT id FROM vault WHERE id = ?", (self.id,)):
			raise PasswordNotFound

	def get(self, _raw: bool = False) -> dict:
		"""Get all info about the password

		Args:
			_raw (bool, optional): Returns the info without decrypting it. Defaults to False.

		Returns:
			dict: The info about the password
		"""		
		# fetch password
		password = dict(get_db(dict).execute(
			"SELECT id, title, url, username, password FROM vault WHERE id = ?",
			(self.id,)
		).fetchone())

		if _raw == False:
			# decrypt everything
			return Crypt(self.key).decrypt(password)

		return dict(password)

	def check(self) -> dict:
		"""Check if the password is considered "safe"

		Returns:
			dict: The check results
		"""		
		password: str = self.get()["password"]
		return _CheckPassword(password).check_password()

	def update(
		self,
		title: str = None,
		url: str = None,
		username: str = None,
		password: str = None,
	) -> dict:
		"""Edit the password

		Args:
			title (str, optional): The new title. Defaults to None.
			url (str, optional): The new url. Defaults to None.
			username (str, optional): The new username. Defaults to None.
			password (str, optional): The new password. Defaults to None.

		Returns:
			dict: The new password info
		"""		
		# encrypt all data
		pw_data = {
			"title": title,
			"url": url,
			"username": username,
			"password": password,
		}
		pw_data = Crypt(self.key).encrypt(pw_data)

		# get current data and update it with new values
		current_data = self.get(_raw=True)
		current_data.update(pw_data)

		# update vault
		get_db().execute(
			"""
			UPDATE vault
			SET title=?, url=?, username=?, password=?
			WHERE id = ?;
		""", (
			current_data["title"],
			current_data["url"],
			current_data["username"],
			current_data["password"],
			self.id
		))

		return self.get()

	def delete(self) -> None:
		"""Delete the password from the vault
		"""		
		get_db().execute("DELETE FROM vault WHERE id = ?", (self.id,))
		return

class Vault:
	"""Represents the vault of the user account
	"""	
	sort_functions = {
		'title': (lambda p: (p['title'], p['username']), False),
		'title_reversed': (lambda p: (p['title'], p['username']), True),
		'date_added': (lambda p: p['id'], False),
		'date_added_reversed': (lambda p: p['id'], True)
	}
	
	def __init__(self, user_id: int, key: bytes):
		self.user_id = user_id
		self.key = key

	def fetchall(self, sort_by: Literal["title", "title_reversed", "date_added", "date_added_reversed"] = "title") -> List[dict]:
		"""Get all passwords from the vault

		Args:
			sort_by (Literal["title", "title_reversed", "date_added", "date_added_reversed"], optional): How to sort the result. Defaults to "title".

		Returns:
			List[dict]: The id, title, url and username of each entry in the vault of the user account
		"""		
		sort_function = self.sort_functions.get(
			sort_by,
			self.sort_functions['title']
		)

		# fetch vault
		passwords: list = get_db(dict).execute(
			f"SELECT id, title, url, username FROM vault WHERE user_id = ?",
			(self.user_id,)
		).fetchall()

		# decrypt everything
		c = Crypt(self.key)
		for i, password in enumerate(passwords):
			passwords[i] = c.decrypt(dict(password))

		# sort result
		passwords.sort(key=sort_function[0], reverse=sort_function[1])

		return passwords

	def search(self, query: str) -> List[dict]:
		"""Search for passwords in the vault

		Args:
			query (str): The term to search for

		Returns:
			List[dict]: All passwords that match. Similar output to self.fetchall
		"""		
		query = query.lower()
		passwords = self.fetchall()
		passwords = list(filter(
			lambda p: (
				query in p["title"].lower()
				or query in p["username"].lower()
				or query in p["url"].lower()
			),
			passwords
		))
		return passwords

	def fetchone(self, id: int) -> Password:
		"""Get one password from the vault

		Args:
			id (int): The id of the password to fetch

		Returns:
			Password: A Password instance of the password
		"""		
		return Password(id, self.key)

	def add(
		self,
		title: str,
		url: str = None,
		username: str = None, password: str = None
	) -> dict:
		"""Add a password to the vault

		Args:
			title (str): The title of the entry
			url (str, optional): The url of the entry. Defaults to None.
			username (str, optional): The username of the entry. Defaults to None.
			password (str, optional): The password of the entry. Defaults to None.

		Returns:
			dict: The info about the new password
		"""		
		# encrypt all data
		pw_data = {
			"title": title,
			"url": url,
			"username": username,
			"password": password,
		}
		pw_data = Crypt(self.key).encrypt(pw_data)

		# insert into vault
		id = get_db().execute("""
			INSERT INTO vault(user_id, title, url, username, password)
			VALUES (?,?,?,?,?);
		""", (
			self.user_id,
			pw_data["title"],
			pw_data["url"],
			pw_data["username"],
			pw_data["password"],
		)).lastrowid

		# return info
		return self.fetchone(id)
