function search(query) {
	fetch('/vault/search?api_key=' + sessionStorage.getItem('api_key') + '&query=' + query, {
		'redirect': 'follow'
	})
	.then(response => {
		// catch errors
		if (!response.ok) {
			return Promise.reject(response.status);
		} else {
			return response.json();
		};
	})
	.then(json => {
		if (json.error === 'redirect to login') {
			window.location.href = '/';
			return
		}
		const data = json.result;
		buildVault(data);
	})
	.catch(e => {
		console.log(e);
	})
}

function checkSearch(e, shortcut=false) {
	if (shortcut === true || e.key === 'Enter') {
		const query = document.getElementById('search-input').value;
		search(query);
	};
}

function buildVault(data) {
	const table = document.getElementById('vault')
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
}

function showNav(e) {
	document.getElementById('nav').classList.toggle('show-nav');
}

function showSearch(e) {
	document.getElementById('search-bar').classList.toggle('show-search');
}

// code run on load

fetch('/vault?api_key=' + sessionStorage.getItem('api_key'), {
	'method': 'POST'
})
.then(response => {
	// catch errors
	if (!response.ok) {
		return Promise.reject(response.status);
	} else {
		return response.json();
	};
})
.then(json => {
	const data = json.result;
	buildVault(data);
})
.catch(e => {
	console.log(e);
})

document.getElementById('search-input').addEventListener('keydown', e => checkSearch(e))

document.getElementById('search-button').addEventListener('click', e => checkSearch(e, true))

document.getElementById('nav-button').addEventListener('click', e => showNav(e))
document.getElementById('search-toggle').addEventListener('click', e => showSearch(e))