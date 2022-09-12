function create() {
	const data = {
		'username': document.getElementById('username-input').value,
		'password': document.getElementById('password-input').value
	};
	fetch(`/api/user/add?username=${data.username}&password=${data.password}`, {
		'method': 'POST'
	})
	.then(response => {return response.json();})
	.then(json => {
		// catch errors
		if (json.error !== null) {
			var el = document.getElementById('username-error');
			if (json.error === 'UsernameInvalid') {
				el.innerText = '*Username invalid';
			} else if (json.error === 'UsernameTaken') {
				el.innerText = '*Username already taken';
			} else {
				el.innerText = '*An error occured';
			};
			el.classList.remove('hidden');
			el.setAttribute('aria-hidden','false');
		} else {
			var el = document.getElementById('username-error');
			el.classList.add('hidden');
			el.setAttribute('aria-hidden','true');
	
			fetch(`/api/auth/login?username=${data.username}&password=${data.password}`, {
				'method': 'POST'
			})
			.then(response => {
				return response.json();
			})
			.then(json => {
				sessionStorage.setItem('api_key', json.result.api_key);
				window.location.href = '/vault';
			})
		};
	})
}

// code run on load

document.getElementById('login-form').setAttribute('action','javascript:create();')
