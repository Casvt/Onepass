// General page functions
function fillUsername() {
	fetch(`/api/auth/status?api_key=${sessionStorage.getItem('api_key')}`)
	.then(response => {
		// catch errors
		if (!response.ok)  {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		document.getElementById('username-title').innerText = json.result.username;
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

function logout() {
	fetch(`/api/auth/logout?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'POST'
	})
	.then(response => {
		hide_windows();
		document.getElementById('loading-title').classList.remove('hidden');
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		cover_and_run(() => {
			window.location.replace('/');
		});
	})
	.catch(e => {
		if (e === 401) {
			cover_and_run(() => {
				window.location.replace('/');
			});
		};
	});
};

// Filling vault
function buildVault(data) {
	const el = document.getElementById('no-password-message');
	if (data.length === 0) {
		// show 'vault empty' message
		el.classList.remove('hidden');
		el.setAttribute('aria-hidden','false');
	} else {
		// hide 'vault empty' message
		el.classList.add('hidden');
		el.setAttribute('aria-hidden','true');
	};

	const table = document.getElementById('vault');
	table.innerHTML = '';
	for (i=0; i<data.length; i++) {
		const obj = data[i];

		const entry = document.createElement("button");
		entry.addEventListener('click', e => showView(obj.id));
		entry.setAttribute('class','vault-entry');
		
		const title = document.createElement("h2");
		title.innerText = obj.title;
		entry.appendChild(title);
		
		const username = document.createElement("p");
		username.innerText = obj.username;
		entry.appendChild(username);
		
		table.appendChild(entry);
	};
};

function fetchVault() {
	const order = document.getElementById('sort-selection').value;
	fetch(`/api/vault?api_key=${sessionStorage.getItem('api_key')}&sort_by=${order}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		buildVault(json.result);
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

// Adding password
function showAdd() {
	hide_windows();
	document.getElementById('add-window').classList.remove('hidden');
	toggle_cover();
};

function addPassword() {
	const data = {
		'title': document.getElementById('title-input').value,
		'url': document.getElementById('url-input').value,
		'username': document.getElementById('username-input').value,
		'password': document.getElementById('password-input').value
	};
	fetch(`/api/vault?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'POST',
		'body': JSON.stringify(data),
		'headers': {'Content-Type': 'application/json'}
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		fetchVault();
		uncover_and_run(() => {
			document.getElementById('title-input').value = '';
			document.getElementById('url-input').value = '';
			document.getElementById('username-input').value = '';
			document.getElementById('password-input').value = '';
		});
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

// Search and sort
function toggleSearch() {
	const cover = document.getElementById('cover').classList
	if (cover.contains('show-search-window')) {
		// hide search
		toggle_search_cover();
	} else {
		// show search
		hide_windows();
		document.getElementById('search-window').classList.remove('hidden');
		toggle_search_cover();
		document.getElementById('search-input').focus();
	};
};

function search() {
	const query = document.getElementById('search-input').value;
	fetch(`/api/vault/search?query=${query}&api_key=${sessionStorage.getItem('api_key')}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		return response.json();
	})
	.then(json => {
		buildVault(json.result);
		toggleSearch();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

function clearSearch() {
	fetchVault();
	document.getElementById('search-input').value = '';
	toggleSearch();
};

function changeOrder() {
	fetchVault();
	toggleSearch();
};

// Viewing password
function showView(id) {
	hide_windows();
	document.getElementById('view-window').classList.remove('hidden');
	
	// fill values
	fetch(`/api/vault/${id}?api_key=${sessionStorage.getItem('api_key')}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		document.getElementById('view-title-input').value = json.result.title;
		document.getElementById('view-url-input').value = json.result.url;
		document.getElementById('view-username-input').value = json.result.username;
		document.getElementById('view-password-input').value = json.result.password;
		document.getElementById('view-id').value = id;
		document.getElementById('check-message').classList.add('hidden');
		
		toggle_cover();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

function editPassword() {
	const data = {
		'title': document.getElementById('view-title-input').value,
		'url': document.getElementById('view-url-input').value,
		'username': document.getElementById('view-username-input').value,
		'password': document.getElementById('view-password-input').value
	};
	const id = document.getElementById('view-id').value;
	fetch(`/api/vault/${id}?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'PUT',
		'body': JSON.stringify(data),
		'headers': {'Content-Type': 'application/json'}
	})
	.then(response => {
		// catch errors 
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		fetchVault();
		toggle_cover();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

function deletePassword() {
	const id = document.getElementById('view-id').value;
	fetch(`/api/vault/${id}?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		fetchVault();
		toggle_cover();
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

function checkPassword() {
	const id = document.getElementById('view-id').value;
	fetch(`/api/vault/${id}/check?api_key=${sessionStorage.getItem('api_key')}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		const el = document.getElementById('check-message');
		el.classList.remove('hidden');
		el.innerText = json.result.message
		if (json.result.place === -1) {
			// password passed check
			el.classList.add('success');
			el.classList.remove('error');
		} else {
			// password failed check
			el.classList.add('error');
			el.classList.remove('success');
		};
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

function showPassword() {
	const el = document.getElementById('view-password-input');
	const icon = document.getElementById('show-password-icon');
	if (el.getAttribute('type') === 'password') {
		// show password
		el.setAttribute('type', 'text');
		icon.src = '/static/img/hide_password.svg';
	} else {
		// hide password
		el.setAttribute('type', 'password');
		icon.src = '/static/img/show_password.svg';
	};
};

// User settings
function showSettings() {
	hide_windows();
	document.getElementById('settings-window').classList.remove('hidden');
	toggle_cover();
};

function showSettingsPassword() {
	const el = document.getElementById('new-password-input');
	const icon = document.getElementById('show-new-password-icon');
	if (el.getAttribute('type') === 'password') {
		// show password
		el.setAttribute('type', 'text');
		icon.src = '/static/img/hide_password.svg';
	} else {
		// hide password
		el.setAttribute('type', 'password');
		icon.src = '/static/img/show_password.svg';
	};
};

function deleteAccount() {
	fetch(`/api/user?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		window.location.href = '/';
		return;
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	});
};

function saveAccount() {
	const data = {
		'new_master_password': document.getElementById('new-password-input').value
	};
	fetch(`/api/user?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'PUT',
		'body': JSON.stringify(data),
		'headers': {'Content-Type': 'application/json'}
	})
	.then(response => {
		window.location.href = '/';
		return;
	});
};

// code run on load

fillUsername();
fetchVault();

// Add eventlisteners
document.getElementById('logout-button').addEventListener('click', e => logout());

document.getElementById('add-button').addEventListener('click', e => showAdd());
document.getElementById('add-form').setAttribute('action', 'javascript:addPassword();');
document.getElementById('cancel-button').addEventListener('click', e => toggle_cover());

document.getElementById('search-button').addEventListener('click', e => toggleSearch());
document.getElementById('search-form').setAttribute('action', 'javascript:search();');
document.getElementById('clear-search-button').addEventListener('click', e => clearSearch());
document.getElementById('sort-selection').addEventListener('change', e => changeOrder());

document.getElementById('view-form').setAttribute('action', 'javascript:editPassword();');
document.getElementById('show-password').addEventListener('click', e => showPassword());
document.getElementById('view-cancel-button').addEventListener('click', e => toggle_cover());
document.getElementById('delete-button').addEventListener('click', e => deletePassword());
document.getElementById('check-button').addEventListener('click', e => checkPassword());

document.getElementById('settings-button').addEventListener('click', e => showSettings());
document.getElementById('settings-form').setAttribute('action', 'javascript:saveAccount();');
document.getElementById('show-new-password').addEventListener('click', e => showSettingsPassword());
document.getElementById('settings-cancel-button').addEventListener('click', e => uncover_and_run(() => {
	document.getElementById('new-password-input').value = '';
}));
document.getElementById('delete-account-button').addEventListener('click', e => deleteAccount());
