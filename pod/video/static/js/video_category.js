// Category to delete
const cat_to_delete = {
    title: undefined,
    slug: undefined
}
const BASE_URL = `${window.location.href}categories/`;

let modal_title = document.querySelector("#manageCategoryModal #modal_title")
let cat_input = document.querySelector("#manageCategoryModal #catTitle");
const formData = new FormData();
const HEADERS = {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest"
}

// Add onclick event to edit a category
let cats_edit = document.querySelectorAll("#my_videos_filter .categories_list_item #edit_category");
cats_edit.forEach(c_e =>{
    c_e.addEventListener('click', (e) =>{
	cat_edit_title = c_e.dataset.title.trim();
	cat_edit_slug = c_e.dataset.slug.trim();
	cat_input.value = cat_edit_title;;
    	modal_title.innerText = c_e.getAttribute('title').trim(); 
    	window.setTimeout(function(){ cat_input.focus()}, 500)
	// add videos of the current category into the dialog
	formData.append("csrfmiddlewaretoken", Cookies.get('csrftoken'));
	const videos = fetch(
		`${BASE_URL}${cat_edit_slug}/`,
		{headers: HEADERS})
		    .then( response =>{
			    response.json().then(data =>{
				    console.log(data);
	    });
	});
	    /*
	const videos2 = CATEGORIES_DATA.find( c =>{
		return c.title === cat_edit_title && c.slug === cat_edit_slug
	});*/
	
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
	c.parentNode.parentNode.querySelectorAll(".categories_list_item").forEach(c_p =>{
	    c_p.classList.remove("active");
	});
	c.parentNode.classList.toggle("active");
	e.stopPropagation();
	// TODO	
    });
});

