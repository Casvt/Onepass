function addPassword() {
	const data = {
		'title': document.getElementById('title-input').value,
		'url': document.getElementById('url-input').value,
		'username': document.getElementById('username-input').value,
		'password': document.getElementById('password-input').value
	}
	fetch(`/api/vault?title=${data.title}&url=${data.url}&username=${data.username}&password=${data.password}&api_key=${sessionStorage.getItem('api_key')}`, {
		'method': 'POST'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};
		return response.json();
	})
	.then(json => {
		window.location.href = `/vault/${json.result.id}`;
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	})
}

// code run on load

document.getElementById('add-form').setAttribute('action','javascript:addPassword();')