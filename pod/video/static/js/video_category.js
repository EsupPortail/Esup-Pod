// Category to delete
const cat_to_delete = {
    title: undefined,
    slug: undefined
}
const BASE_URL = `${window.location.href}categories/`;
// edit and filter make the same request, prev_data save the first results
const SAVED_DATA = {};
let saveCatBtn = document.querySelector("#manageCategoryModal #saveCategory" ) // btn in dialog
let modal_title = document.querySelector("#manageCategoryModal #modal_title")
let cat_input = document.querySelector("#manageCategoryModal #catTitle");
let CURR_CATEGORY = {};
const formData = new FormData();
const HEADERS = {
    //"Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "X-CSRFToken": Cookies.get("csrftoken"),
    //"Accept": "application/json"
}

// Check in CATEGORIES_DATA if the cat exists
let catExists = (c_slug) =>{
    return Object.keys(CATEGORIES_DATA.find(c=> c.slug==="1-second")).length > 0;
}

// Save/update category data locally
let saveCategoryData = (data)=>{
    SAVED_DATA[`${data.slug}`] = data;
}

// Delete category data locally
let deleteFromSaveData = (c_slug)=>{
    if(Object.keys(SAVED_DATA).includes(c_slug))
	delete SAVED_DATA[c_slug];
}

// Get saved category data
let  getSavedData = (c_slug) =>{
    if(Object.keys(SAVED_DATA).includes(c_slug))
	return SAVED_DATA[c_slug];

    return {};
}
// Add event toggle selected class on el
let toggleSelectedClass = (el)=>{
    el.addEventListener('click', e=>{
        e.preventDefault();
        e.stopPropagation();
        el.classList.toggle("selected");
    });
}
// Make requets => get category data
let fetchCategoryData = async (cat_slug) =>{
    try
    {
        let resp = await fetch(`${BASE_URL}${cat_slug}/`,{headers: HEADERS});
        return await resp.json();
    } 
    catch(e) {console.error(e.message);}
}
let get_type_icon = (is_video=true)=>{
    let videoContent_Text = gettext("Video content.");
    let audioContent_Text = gettext("Audio content.");
    if(is_video)
	return `<span title="${videoContent_Text}">
		    <i data-feather="film"></i>
		</span>`;
    return `<span title="${audioContent_Text}">
		<i data-feather="radio"></i>
	    </span>`;
}
let getModalVideoCard = (v)=>{
    return `
        <div class="checked_overlay">
	    <span class="card_selected" id="card_selected">
	        <svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="check-circle" class="svg-inline--fa fa-check-circle fa-w-16" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="currentColor" d="M504 256c0 136.967-111.033 248-248 248S8 392.967 8 256 119.033 8 256 8s248 111.033 248 248zM227.314 387.314l184-184c6.248-6.248 6.248-16.379 0-22.627l-22.627-22.627c-6.248-6.249-16.379-6.249-22.628 0L216 308.118l-70.059-70.059c-6.248-6.248-16.379-6.248-22.628 0l-22.627 22.627c-6.248 6.248-6.248 16.379 0 22.627l104 104c6.249 6.249 16.379 6.249 22.628.001z"></path></svg>
	    </span>
	</div>
	<div class="card modal_category_card mb-4 box-shadow border-secondary video-card">
	    <div class="card-header" style="">
	        <div class="d-flex justify-content-between align-items-center">
		    <small class="text-muted time">${v.duration}</small>
		    <span class="text-muted small">
		        ${get_type_icon(v.is_video)}
		    </span>
		</div>
	    </div>
	    <div class="card-body">
	        <a class="link-center-pod" href="#" title="${v.title}">
		    ${v.thumbnail}
		</a>
	    </div>
	    <div class="card-footer">
	        <span class="video_title">${v.title}</span>
	    </div>
	</div>`
}
// Append video card in category modal
let appendVideoCard = (v)=>{
    let modalListVideo = document.querySelector("#manageCategoryModal .category_modal_video_list");
    let videoCard = getModalVideoCard(v);
    let v_wrapper = document.createElement("Div");
    v_wrapper.setAttribute("data-slug", v.slug);
    v_wrapper.setAttribute("class", "infinite-item col-12 col-md-6 col-lg-3 mb-2 card-group selected")
    v_wrapper.innerHTML = videoCard;
    modalListVideo.appendChild(v_wrapper);
    // set click event listener
    toggleSelectedClass(v_wrapper);
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

    	saveCatBtn.setAttribute("data-action", "edit")
	let jsonData = getSavedData(cat_edit_slug);
    	CURR_CATEGORY_SLUG = jsonData;
	if( Object.keys(jsonData).length )
	{
	    jsonData.videos.forEach(v=>{
		appendVideoCard(v);
	    });
	}
	else
	{
	    jsonData = fetchCategoryData(cat_edit_slug);
	    jsonData.then( data =>{
	        data.videos.forEach(v=>{
		    appendVideoCard(v);
	        });
    		CURR_CATEGORY = data;
		// save data
		saveCategoryData(data);
	    });
	}
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


// Add onclick event to save category (create or edit) data
saveCatBtn.addEventListener("click", e=>{
    e.preventDefault()
    e.stopPropagation()
    let videos = Array.from(document.querySelectorAll(".category_modal_video_list .selected")).map(v_el => v_el.dataset.slug.trim());
    console.log("Videos to save ")
    console.table(videos)
    console.table(CURR_CATEGORY)
    if(Object.keys(CURR_CATEGORY).length > 0) // Editing mode
    {
	 postData = {
	    title: cat_input.value.trim(),
	    videos: videos
	 }
	// make fetch request to save new data
	fetch(`${BASE_URL}edit/${CURR_CATEGORY.slug}/` , {
	    method: "POST",
	    body: JSON.stringify(postData),
	    headers: HEADERS
	}).then(response =>{
	    response.json().then(data=>{
		deleteFromSaveData(CURR_CATEGORY.slug);
		saveCategoryData(data);
		CURR_CATEGORY = {};
	    })
	}).catch(err =>{
	    console.log(err);
	});
    }
    else // Adding mode
    { 
	console.log("ADDING MODE")
    }

    // UPDATE SAVED DATA
    console.log("Saving");
    document.querySelector("#manageCategoryModal #cancelDialog").click()
});

// Add onclick event to add a new category
let add_cat = document.querySelector('#my_videos_filter #add_category_btn');
add_cat.addEventListener('click', e=>{
    modal_title.innerText = add_cat.getAttribute('title').trim(); 
    cat_input.value = "";
    // set Save button text to 'create category'
    saveCatBtn.textContent = gettext("Create category");
    saveCatBtn.setAttribute("data-action", "create");
    CURR_CATEGORY = null;
    window.setTimeout(function(){ cat_input.focus()}, 500)
});


// Add onclick event to each video in category modal
let videos_in_modal = document.querySelectorAll("#manageCategoryModal .infinite-item");
videos_in_modal.forEach(v => {
    toggleSelectedClass(v)
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
	let cat_filter_slug = c.dataset.slug;
	fetch(`${BASE_URL}${cat_filter_slug}/`, {headers: HEADERS}).then(response =>{
	    response.json().then(data=>{
		console.log(data);
	    });
	});
    });
});

