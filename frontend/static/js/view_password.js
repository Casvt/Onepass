function togglePassword() {
	const input = document.getElementById('password-input');
	const button = document.getElementById('show-password-button');
	const icon = document.getElementById('show-password-icon');
	if (input.getAttribute('type') === 'password') {
		// show password
		input.setAttribute('type', 'text');
		button.setAttribute('aria-label', 'Hide password');
		icon.setAttribute('src', '/static/img/hide_password.svg');
		icon.setAttribute('aria-label', 'Hide password icon');
	} else {
		// hide password
		input.setAttribute('type', 'password');
		button.setAttribute('aria-label', 'Show password');
		icon.setAttribute('src', '/static/img/show_password.svg');
		icon.setAttribute('aria-label', 'Show password icon');
	};
}

function editPassword() {
	const data = {
		'title': document.getElementById('title-input').value,
		'url': document.getElementById('url-input').value,
		'username': document.getElementById('username-input').value,
		'password': document.getElementById('password-input').value
	}
	fetch(`/api/vault/${id}?title=${data.title}&url=${data.url}&username=${data.username}&password=${data.password}&api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'PUT'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		window.location.href = `/vault/${id}`
	})
	.catch(e => {
		if (e === 404) {
			window.location.href = '/vault';
		} else if (e === 401) {
			window.location.href = '/';
		};
	})
}

function deletePassword() {
	fetch(`/api/vault/${id}?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		window.location.href = '/vault';
	})
	.catch(e => {
		if (e === 404) {
			window.location.href = '/vault';
		} else if (e === 401) {
			window.location.href = '/';
		};
	})
}

// code run on load

const id = window.location.pathname.split('/').at(-1)
fetch(`/api/vault/${id}?api_key=${sessionStorage.getItem('api_key')}`)
.then(response => {
	// catch errors
	if (!response.ok) {
		return Promise.reject(response.status);
	};

	return response.json();
})
.then(json => {
	const data = json.result;
	document.getElementById('title-input').value = data.title;
	document.getElementById('url-input').value = data.url;
	document.getElementById('username-input').value = data.username;
	document.getElementById('password-input').value = data.password;
})
.catch(e => {
	if (e === 404) {
		window.location.href = '/not-found';
	} else if (e === 401) {
		window.location.href = '/';
	};
})

document.getElementById('show-password-button').addEventListener('click', e => togglePassword())
document.getElementById('delete-button').addEventListener('click', e => deletePassword())
document.getElementById('edit-form').setAttribute('action','javascript:editPassword();')