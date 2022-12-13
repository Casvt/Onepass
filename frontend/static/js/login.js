function login() {
	const data = {
		'username': document.getElementById('username-input').value,
		'master_password': document.getElementById('password-input').value
	};
	fetch(`/api/auth/login`, {
		'method': 'POST',
		'body': JSON.stringify(data),
		'headers': {'Content-Type': 'application/json'}
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		
		// Hide any errors that were showing
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

		cover_and_run(() => {
			window.location.href = '/vault';
		});
	})
	.catch(e => {
		if (e === 404) {
			// Username not found
			var el = document.getElementById('username-error');
			el.classList.remove('hidden');
			el.setAttribute('aria-hidden','false');
			var el = document.getElementById('password-error');
			el.classList.add('hidden');
			el.setAttribute('aria-hidden','true');
		} else if (e === 401) {
			// Password incorrect
			var el = document.getElementById('password-error');
			el.classList.remove('hidden');
			el.setAttribute('aria-hidden','false');
			var el = document.getElementById('username-error');
			el.classList.add('hidden');
			el.setAttribute('aria-hidden','true');
		};
	});
};

function create() {
	const data = {
		'username': document.getElementById('create-username-input').value,
		'master_password': document.getElementById('create-password-input').value
	};
	fetch(`/api/user/add`, {
		'method': 'POST',
		'body': JSON.stringify(data),
		'headers': {'Content-Type': 'application/json'}
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		return response.json();
	})
	.then(json => {
		fetch(`/api/auth/login`, {
			'method': 'POST',
			'body': JSON.stringify(data),
			'headers': {'Content-Type': 'application/json'}
		})
		.then(response => {
			return response.json();
		})
		.then(json => {
			sessionStorage.setItem('api_key', json.result.api_key);
			
			cover_and_run(() => {
				window.location.href = '/vault';
			});
		});
	});
};

function toggleWindow() {
	document.getElementById('window').classList.remove('show-window');
	setTimeout(() => {
		document.getElementById('login-container').classList.toggle('hidden');
		document.getElementById('create-container').classList.toggle('hidden');	
		document.getElementById('window').classList.add('show-window');
	}, 600);
}

// code run on load

setTimeout(() => {
	document.getElementById('window').classList.add('show-window');
	setTimeout(() => {
		document.getElementById('username-input').focus();
	}, 600);
}, 500);

document.getElementById('login-form').setAttribute('action','javascript:login();');
document.getElementById('create-link').addEventListener('click', e => toggleWindow());
document.getElementById('create-form').setAttribute('action', 'javascript:create();');
document.getElementById('login-link').addEventListener('click', e => toggleWindow());
