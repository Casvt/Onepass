function passwordShortcut(e) {
	if (e.key === 'Enter') {
		document.getElementById('password-input').blur();
		checkPassword();
	};
}

function checkPassword() {
	const password = document.getElementById('password-input').value;
	fetch(`/api/vault/check?password=${password}&api_key=${sessionStorage.getItem('api_key')}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		if (json.result.message === 'No problems found with password!') {
			document.getElementById('password-error').classList.add('hidden');
			document.getElementById('password-success').classList.remove('hidden');
		} else {
			document.getElementById('password-success').classList.add('hidden');
			document.getElementById('password-error').classList.remove('hidden');
			document.getElementById('password-error').innerText = json.result.message;
		};
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	})
}

// code run on load

document.getElementById('login-form').setAttribute('action','javascript:checkPassword();')
document.getElementById('password-input').addEventListener('keydown', e => passwordShortcut(e))
