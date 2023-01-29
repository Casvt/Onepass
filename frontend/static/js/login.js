const elements = {
	'window': document.getElementById('window'),
	'containers': document.querySelectorAll('[id$="-container"]'),

	'username': document.getElementById('username-input'),
	'password': document.getElementById('password-input'),
	'username_new': document.getElementById('create-username-input'),
	'password_new': document.getElementById('create-password-input'),

	'username_error': document.getElementById('username-error'),
	'password_error': document.getElementById('password-error'),
	'username_taken': document.getElementById('taken-username-error'),
	'username_invalid': document.getElementById('invalid-username-error')
};

function toggleElement(el, state=null) {
	if (state === 'show' || (el.classList.contains('hidden') && state === null)) {
		// Show element
		el.classList.remove('hidden');
		el.setAttribute('aria-hidden', 'false');
	} else {
		// Hide element
		el.classList.add('hidden');
		el.setAttribute('aria-hidden', 'true');
	};
	return;
};

function login() {
	const data = {
		'username': elements.username.value,
		'master_password': elements.password.value
	};
	fetch(`/api/auth/login`, {
		'method': 'POST',
		'body': JSON.stringify(data),
		'headers': {'Content-Type': 'application/json'}
	})
	.then(response => {
		// Hide any errors that were showing
		toggleElement(elements.username_error, 'hide');
		toggleElement(elements.password_error, 'hide');
		elements.username.classList.remove('error-input');
		elements.password.classList.remove('error-input');

		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		return response.json();
	})
	.then(json => {
		sessionStorage.setItem('api_key', json.result.api_key);

		cover_and_run(() => {
			window.location.href = '/vault';
		});
	})
	.catch(e => {
		if (e === 404) {
			// Username not found
			toggleElement(elements.username_error, 'show');
			toggleElement(elements.password_error, 'hide');
			elements.username.classList.add('error-input');
		} else if (e === 401) {
			// Password incorrect
			toggleElement(elements.username_error, 'hide');
			toggleElement(elements.password_error, 'show');
			elements.password.classList.add('error-input');
		};
	});
};

function create() {
	const data = {
		'username': elements.username_new.value,
		'master_password': elements.password_new.value
	};
	fetch(`/api/user/add`, {
		'method': 'POST',
		'body': JSON.stringify(data),
		'headers': {'Content-Type': 'application/json'}
	})
	.then(response => {
		// Hide any errors that were showing
		toggleElement(elements.username_invalid, 'hide');
		toggleElement(elements.username_taken, 'hide');
		elements.username_new.classList.remove('error-input');
		elements.password_new.classList.remove('error-input');

		return response.json();
	})
	.then(json => {
		// catch errors
		if (json.error !== null) {
			return Promise.reject(json);
		};

		elements.username.value = data.username;
		elements.password.value = data.master_password;
		login();
		return;
	})
	.catch(json => {
		if (json.error === 'UsernameInvalid') {
			// Username invalid
			toggleElement(elements.username_invalid, 'show');
			toggleElement(elements.username_taken, 'hide');
			elements.username_new.classList.add('error-input');
		} else if (json.error === 'UsernameTaken') {
			// Username taken
			toggleElement(elements.username_invalid, 'hide');
			toggleElement(elements.username_taken, 'show');
			elements.username_new.classList.add('error-input');
		};
	});
};

function toggleWindow() {
	elements.window.classList.remove('show-window');
	setTimeout(() => {
		elements.containers.forEach(c => c.classList.toggle('hidden'));
		elements.window.classList.add('show-window');
	}, 600);
}

// code run on load

setTimeout(() => {
	elements.window.classList.add('show-window');
	setTimeout(() => {
		elements.username.focus();
	}, 600);
}, 500);

document.getElementById('login-form').setAttribute('action','javascript:login();');
document.getElementById('create-link').addEventListener('click', e => toggleWindow());
document.getElementById('create-form').setAttribute('action', 'javascript:create();');
document.getElementById('login-link').addEventListener('click', e => toggleWindow());
