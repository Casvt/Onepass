function showNav(e) {
	document.getElementById('nav').classList.toggle('show-nav');
}

function editAccount() {
	const data = {
		'old_password': document.getElementById('old_password').value,
		'new_password': document.getElementById('new_password').value
	};
	fetch(`/api/user?old_password=${data.old_password}&new_password=${data.new_password}&api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'PUT'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		logout(response);
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		} else if (e === 400) {
			var el = document.getElementById('password-error');
			el.classList.remove('hidden');
			el.setAttribute('aria-hidden','false');
		}
	})
}

function deleteAccount() {
	fetch(`/api/user?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'DELETE'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		window.location.href = '/'
	})
	.catch(e => {
		console.log(e);
	})
}

function logout(e) {
	fetch(`/api/auth/logout?api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'POST'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		window.location.replace('/');
	})
	.catch(e => {
		if (e === 401) {
			window.location.replace('/');
		};
	})
}

// code run on load

document.getElementById('logout-button').addEventListener('click', e => logout(e))
document.getElementById('nav-button').addEventListener('click', e => showNav(e))
document.getElementById('reset-form').setAttribute('action','javascript:editAccount();')
document.getElementById('delete-account').addEventListener('click', e => deleteAccount(e))
