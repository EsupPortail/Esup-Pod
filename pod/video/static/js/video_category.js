// Category to delete
const cat_to_delete = {
    title: undefined,
    slug: undefined
}
const BASE_URL = `${window.location.href}category/`;

let modal_title = document.querySelector("#manageCategoryModal #modal_title")
let cat_input = document.querySelector("#manageCategoryModal #catTitle");

// Add onclick event to edit a category
let cats_edit = document.querySelectorAll("#my_videos_filter .categories_list_item #edit_category");
cats_edit.forEach(c_e =>{
    c_e.addEventListener('click', (e) =>{
	cat_input.value = c_e.dataset.title.trim();
    	modal_title.innerText = c_e.getAttribute('title').trim(); 
    	window.setTimeout(function(){ cat_input.focus()}, 500)
    });
});

// Add onclick event to delete a category
let cats_del = document.querySelectorAll("#my_videos_filter .categories_list_item #remove_category_icon");
cats_del.forEach(c_d => {
    c_d.addEventListener('click', (e) =>{
	// Show confirm modal => manage by boostrap
	cat_to_delete.title = c_d.dataset.title;
	cat_to_delete.slug = c_d.dataset.slug;
    });
});

// Add onclick event to delete a category
let del_cat = document.querySelector("#confirm_remove_category_btn");
del_cat.addEventListener('click', (e) =>{
	console.log(cat_to_delete)
    if(cat_to_delete.title && cat_to_delete.slug)
    {
	// Delete category
	let cat = CATEGORIES_DATA.find(c =>{
	    return c.title === cat_to_delete.title && c.slug === cat_to_delete.slug;
	});
	if(cat)
	{
	    let url = `${BASE_URL}delete/${cat.id}`;
	    console.log("----------------------------------------")
	    console.log(url)
 	    console.log("----------------------------------------")
	    // Ajax request to delete category
	}
    }
    else
    { 
	// display msg error like 'no category to delete'
    }
});


// Add onclick event to add a new category
let add_cat = document.querySelector('#my_videos_filter #add_category_btn');
add_cat.addEventListener('click', e=>{
    modal_title.innerText = add_cat.getAttribute('title').trim(); 
    cat_input.value = "";
    window.setTimeout(function(){ cat_input.focus()}, 500)
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

