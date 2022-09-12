function search(query) {
	fetch(`/api/vault/search?query=${query}&api_key=${sessionStorage.getItem('api_key')}`)
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		};

		return response.json();
	})
	.then(json => {
		buildVault(json.result);
	})
	.catch(e => {
		if (e === 401) {
			window.location.href = '/';
		};
	})
}

function checkSearch(e, shortcut=false) {
	if (shortcut === true || e.key === 'Enter') {
		const query = document.getElementById('search-input').value;
		search(query);
	};
}

function buildVault(data) {
	const table = document.getElementById('vault');
	const el = document.getElementById('no-result-error');
	table.innerHTML = '';
	for (i=0; i<data.length; i++) {
		const obj = data[i];

		const entry = document.createElement("a");
		entry.setAttribute('href', `/vault/${obj.id}`)
		entry.setAttribute('class','vault-entry');
		
		const title = document.createElement("h2");
		title.innerText = obj.title;
		entry.appendChild(title);
		
		const username = document.createElement("p");
		username.innerText = obj.username;
		entry.appendChild(username);
		
		table.appendChild(entry);
	};

	if (table.innerHTML === '') {
		el.classList.remove('hidden');
		el.setAttribute('aria-hidden','false');
	} else {
		el.classList.add('hidden');
		el.setAttribute('aria-hidden','true');
	};
}

function showNav(e) {
	document.getElementById('nav').classList.toggle('show-nav');
}

function showSearch(e) {
	document.getElementById('search-bar').classList.toggle('show-search');
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

fetch(`/api/vault?api_key=${sessionStorage.getItem('api_key')}`)
.then(response => {
	// catch errors
	if (!response.ok) {
		return Promise.reject(response.status);
	};
	return response.json();
})
.then(json => {
	buildVault(json.result);
})
.catch(e => {
	if (e === 401) {
		window.location.href = '/';
	};
})

document.getElementById('logout-button').addEventListener('click', e => logout(e))
document.getElementById('search-input').addEventListener('keydown', e => checkSearch(e))
document.getElementById('search-button').addEventListener('click', e => checkSearch(e, true))
document.getElementById('nav-button').addEventListener('click', e => showNav(e))
document.getElementById('search-toggle').addEventListener('click', e => showSearch(e))