function cover_and_run(f) {
	document.getElementById('cover').classList.add('show-window');
	setTimeout(f, 1000);
};

function uncover_and_run(f) {
	document.getElementById('cover').classList.remove('show-window');
	setTimeout(f, 1000);
};

function toggle_cover() {
	document.getElementById('cover').classList.toggle('show-window');
};

function toggle_search_cover() {
	document.getElementById('cover').classList.toggle('show-search-window');
};

function hide_windows() {
	document.querySelectorAll('.cover-entry').forEach(el => {
		el.classList.add('hidden');
	});
	document.getElementById('cover').classList.remove('show-search-window','show-window');
};

// code run on load

setTimeout(() => {
	document.getElementById('cover').classList.remove('show-window')
}, 350);
