if (sessionStorage.getItem('api_key') === null) {
	window.location.href = '/';
}

fetch('/?api_key=' + sessionStorage.getItem('api_key'), {
	'method': 'PUT'
})
.then(response => {
	return response.text()
})
.then(text => {
	if (text === 'INVALID') {
		window.location.href = '/';
		return
	};
})

const input = document.getElementById('apikey-input')
if (input != null) {
	input.value = sessionStorage.getItem('api_key');
}