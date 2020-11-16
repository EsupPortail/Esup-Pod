let modal_title = document.querySelector("#manageCategoryModal #modal_title")
let cat_input = document.querySelector("#manageCategoryModal #catTitle");

// Add onclick event to each category
let cats_edit = document.querySelectorAll("#my_videos_filter .categories_list_item .edit_category");
cats_edit.forEach(c_e =>{
    c_e.addEventListener('click', (e) =>{
	let c = c_e.parentNode.querySelector('.cat_title');
	cat_input.value = c.textContent.trim();
    	modal_title.innerText = c_e.getAttribute('title').trim(); 
    	window.setTimeout(function(){ console.log("OKKKKKKK"); cat_input.focus()}, 500)
    });
});

// Add onclick event to add new category
let add_cat = document.querySelector('#my_videos_filter #add_category_btn');
add_cat.addEventListener('click', e=>{
    modal_title.innerText = add_cat.getAttribute('title').trim(); 
    cat_input.value = "";
    window.setTimeout(function(){ console.log("OKKKKKKK"); cat_input.focus()}, 500)
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

