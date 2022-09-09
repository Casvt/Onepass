function showNav(e) {
	document.getElementById('nav').classList.toggle('show-nav');
}

function deleteAccount() {
	var username = document.getElementById('username').value;
	var password = document.getElementById('password').value;
	fetch(`/settings?username=${username}&password=${password}`, {
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

// code run on load

document.getElementById('delete-form').setAttribute('action','javascript:deleteAccount();')
document.getElementById('nav-button').addEventListener('click', e => showNav(e))
