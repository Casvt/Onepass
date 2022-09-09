document.getElementById('login-form').setAttribute('action','javascript:login();')

function login() {
	const data = {
		'username': document.getElementById('username-input').value,
		'password': document.getElementById('password-input').value
	};
	fetch('/', {
		'method': 'POST',
		'body': JSON.stringify(data)
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		document.getElementById('username-error').classList.add('hidden');
		document.getElementById('password-error').classList.add('hidden');

		return response.json();
	})
	.then(json => {
		sessionStorage.setItem('api_key', json.result.api_key);
		window.location.href = '/vault';
	})
	.catch(e => {
		if (e === 404) {
			const el = document.getElementById('username-error');
			el.innerText = '*Username not found';
			el.classList.remove('hidden');
			document.getElementById('password-error').classList.add('hidden');
		} else if (e === 401) {
			const el = document.getElementById('password-error');
			el.innerText = '*Password incorrect';
			el.classList.remove('hidden');
			document.getElementById('username-error').classList.add('hidden');
		};
	})
}