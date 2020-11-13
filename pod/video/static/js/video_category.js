// Add onclick event to each category
let cats_edit = document.querySelectorAll("#my_videos_filter .categories_list_item .edit_category");
let cat_input = document.querySelector("#manageCategoryModal #catTitle");

cats_edit.forEach(c_e =>{
    c_e.addEventListener('click', (e) =>{
	let c = c_e.parentNode.querySelector('.cat_title');
	cat_input.value = c.textContent.trim();
	window.setInterval(function(){ cat_input.focus();}, 10)
    });
});

// Add onclick event to each video in category modal
let videos_in_modal = document.querySelectorAll("#manageCategoryModal .infinite-item");
videos_in_modal.forEach(v => {
    v.addEventListener('click', e=>{
	e.preventDefault();
	e.stopPropagation();
	v.classList.toggle('selected');
    });
});

// Add click event on category in filter bar to filter videos in my_videos vue
let cats = document.querySelectorAll("#my_videos_filter .categories_list_item .cat_title");
cats.forEach(c =>{
    c.addEventListener('click', e =>{
	e.stopPropagation();
	// TODO	
    });
});

