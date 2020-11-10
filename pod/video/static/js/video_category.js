let cats_edit = document.querySelectorAll("#my_videos_filter .categories_list_item .edit_category");
let cat_input = document.querySelector("#manageCategoryModal #catTitle");
// Add onclick event to each category
cats_edit.forEach(c_e =>{
    c_e.addEventListener('click', (e) =>{
	let c = c_e.parentNode.querySelector('.cat_title');
	cat_input.value = c.textContent.trim();	
    });
});

let videos_in_modal = document.querySelectorAll("#manageCategoryModal .infinite-item");

videos_in_modal.forEach(v => {
    v.addEventListener('click', e=>{
	e.preventDefault();
	e.stopPropagation();
	v.classList.toggle('selected');
    });
});
