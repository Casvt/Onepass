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

function deletePassword() {
	fetch(`/vault/${id}?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		} else {
			return response.json();
		};
	})
	.then(json => {
		if (json.error === 'redirected to login') {
			window.location.href = '/';
		} else {
			window.location.href = '/vault';
		};
		return
	})
	.catch(e => {
		console.log(e);
		if (e === 404) {
			window.location.href = '/not-found';
		};
	})
}

const id = window.location.pathname.split('/').at(-1)
fetch(`/vault/${id}?api_key=${sessionStorage.getItem('api_key')}`, {
	'method': 'PUT'
})
.then(response => {
	// catch errors
	if (!response.ok) {
		return Promise.reject(response.status);
	} else {
		return response.json();
	};
})
.then(json => {
	if (json.error === 'redirect to login') {
		window.location.href = '/';
		return
	}
	const data = json.result;
	document.getElementById('title-input').value = data.title;
	document.getElementById('url-input').value = data.url;
	document.getElementById('username-input').value = data.username;
	document.getElementById('password-input').value = data.password;
})
.catch(e => {
	console.log(e);
	if (e === 404) {
		window.location.href = '/not-found';
	};
})

document.getElementById('show-password-button').addEventListener('click', e => togglePassword())
document.getElementById('delete-button').addEventListener('click', e => deletePassword())