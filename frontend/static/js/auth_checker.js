// this script is included in some html documents to run on load
// this acts as a check for authentication
// this is not needed everywhere because often there is already a request being made on load that handles it
// if this script is included, it means that no request is made on load (to check auth) so this script will do it then

// code run on load

fetch(`/api/auth/status?api_key=${sessionStorage.getItem('api_key')}`)
.then(response => {
	// catch errors
	if (!response.ok) {
		return Promise.reject(response.status);
	};
	return
})
.catch(e => {
	if (e === 401) {
		window.location.href = '/';
	};
})