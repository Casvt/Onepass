function login() {
	const data = {
		'username': document.getElementById('username-input').value,
		'password': document.getElementById('password-input').value
	};
	fetch(`/api/auth/login?username=${data.username}&password=${data.password}`, {
		'method': 'POST'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		var el = document.getElementById('username-error');
		el.classList.add('hidden');
		el.setAttribute('aria-hidden','true');
		var el = document.getElementById('password-error');
		el.classList.add('hidden');
		el.setAttribute('aria-hidden','true');

		return response.json();
	})
	.then(json => {
		sessionStorage.setItem('api_key', json.result.api_key);
		window.location.href = '/vault';
	})
	.catch(e => {
		if (e === 404) {
			var el = document.getElementById('username-error');
			el.innerText = '*Username not found';
			el.classList.remove('hidden');
			el.setAttribute('aria-hidden','false');
			var el = document.getElementById('password-error');
			el.classList.add('hidden');
			el.setAttribute('aria-hidden','true');
		} else if (e === 401) {
			var el = document.getElementById('password-error');
			el.innerText = '*Password incorrect';
			el.classList.remove('hidden');
			el.setAttribute('aria-hidden','false');
			var el = document.getElementById('username-error');
			el.classList.add('hidden');
			el.setAttribute('aria-hidden','true');
		};
	})
}

// code run on load

document.getElementById('login-form').setAttribute('action','javascript:login();')
