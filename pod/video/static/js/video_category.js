(function(CATEGORIES_DATA){
    // Category to delete
    const CAT_TO_DELETE = {
	slug: undefined,
	html: undefined
    }
    const BASE_URL = `${window.location.href}categories/`;
    // To prevent too many requests to the server
    const SAVED_DATA = {};
    let saveCatBtn = document.querySelector("#manageCategoryModal #saveCategory" ) // btn in dialog
    let modal_title = document.querySelector("#manageCategoryModal #modal_title")
    let cat_input = document.querySelector("#manageCategoryModal #catTitle");
    let CURR_CATEGORY = {}; // current editing category (js object)
    let DOMCurrentEditCat = null; // current editing category (html DOM)
    const formData = new FormData();
    const HEADERS = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": Cookies.get("csrftoken"),
        "Accept": "application/json"
    }

    // Search categery
    let searchCatInput = document.querySelector("#my_videos_filter #searchcategories");
    let filterCatHandler = (s) =>{
	let cats = document.querySelectorAll(".categories_list .cat_title:not(.hidden)");
	if(s.length >= 3)
	{
	    cats.forEach( cat =>{
	        if( !cat.getAttribute('title').trim().toLowerCase().includes(s) )
		    cat.parentNode.classList.add('hidden');
	    });
	}
	else
	{
	    cats = document.querySelectorAll(".categories_list .hidden");
	    cats.forEach( cat =>{
		cat.classList.remove('hidden');
	    });
	}
    }
    searchCatInput.addEventListener('input', e =>{
	console.log("INPUT HANDLER");
	filterCatHandler(searchCatInput.value.trim());
    });

    // remove all current selected videos in dialog
    let refreshDialog = () =>{
	    console.log("REFRESH");
	let videos = document.querySelectorAll(".category_modal_video_list .selected");
	videos.forEach(v =>{ v.parentNode.removeChild(v) });
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
    let deleteFromSavedData = (c_slug)=>{
        if(Object.keys(SAVED_DATA).includes(c_slug))
            delete SAVED_DATA[c_slug];
    }
    
    // Search cat by slug
    let findCategory = (slug) =>{
	let cat = CATEGORIES_DATA.find(c=> c.slug===slug)
	if(Object.keys(cat).length)
	    return cat;
	return getSavedData(slug);
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

    // Make post request. for edit or add category, postData(object)
    let postCategoryData = async (url, postData) =>{
	try
	{
            let resp = await fetch(url, {method: "POST", body: JSON.stringify(postData), headers: HEADERS});
	    return await resp.json();
        }
	catch(e){console.error(e.message);}
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
    
    // Create category html element <li></li>
    let getCategoryLi = (title, slug) =>{
        let spanEdit = document.createElement('span');
	spanEdit.setAttribute('title', gettext("Edit the category"));
	spanEdit.setAttribute('data-toggle', 'modal');
	spanEdit.setAttribute('data-target', '#manageCategoryModal');
	spanEdit.setAttribute('data-slug', slug);
	spanEdit.setAttribute('data-title', title);
	spanEdit.setAttribute('class', 'edit_category');
	spanEdit.setAttribute('id', 'edit_category');
	spanEdit.innerHTML = `
	    <svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="edit" class="svg-inline--fa fa-edit fa-w-18" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512"><path fill="currentColor" d="M402.6 83.2l90.2 90.2c3.8 3.8 3.8 10 0 13.8L274.4 405.6l-92.8 10.3c-12.4 1.4-22.9-9.1-21.5-21.5l10.3-92.8L388.8 83.2c3.8-3.8 10-3.8 13.8 0zm162-22.9l-48.8-48.8c-15.2-15.2-39.9-15.2-55.2 0l-35.4 35.4c-3.8 3.8-3.8 10 0 13.8l90.2 90.2c3.8 3.8 10 3.8 13.8 0l35.4-35.4c15.2-15.3 15.2-40 0-55.2zM384 346.2V448H64V128h229.8c3.2 0 6.2-1.3 8.5-3.5l40-40c7.6-7.6 2.2-20.5-8.5-20.5H48C21.5 64 0 85.5 0 112v352c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48V306.2c0-10.7-12.9-16-20.5-8.5l-40 40c-2.2 2.3-3.5 5.3-3.5 8.5z"></path></svg>
	`;
	editHandler(spanEdit);

        let spanDelete = document.createElement('span');
	spanDelete.setAttribute('title', gettext("Delete the category"));
	spanDelete.setAttribute('data-toggle', 'modal');
	spanDelete.setAttribute('data-target', '#deleteCategoryModal');
	spanDelete.setAttribute('data-slug', slug);
	spanDelete.setAttribute('data-title', title);
	spanDelete.setAttribute('class', 'remove_category');
	spanDelete.setAttribute('id', 'edit_category');
	spanDelete.innerHTML = `
	    <svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="trash-alt" class="svg-inline--fa fa-trash-alt fa-w-14" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="currentColor" d="M32 464a48 48 0 0 0 48 48h288a48 48 0 0 0 48-48V128H32zm272-256a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zm-96 0a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zm-96 0a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zM432 32H312l-9.4-18.7A24 24 0 0 0 281.1 0H166.8a23.72 23.72 0 0 0-21.4 13.3L136 32H16A16 16 0 0 0 0 48v32a16 16 0 0 0 16 16h416a16 16 0 0 0 16-16V48a16 16 0 0 0-16-16z"></path></svg>
	`;
	deleteHandler(spanDelete);

	let li = document.createElement('li');
	li.setAttribute("class", "categories_list_item");
	li.innerHTML = `
	    <span class="cat_title" title="First Category" data-slug="1-first-category">
		${title}
	    </span>
	    <div class="category_actions">
            </div>`;
	li.querySelector(".category_actions").appendChild(spanEdit);
	li.querySelector(".category_actions").appendChild(spanDelete);
	return li;
    }

    // Create video card for Category Dialog
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

    // Handler to delete category, c_d=current category to delete
    let deleteHandler = (c_d) =>{
	c_d.addEventListener('click', (e) =>{
 	    // Show confirm modal => manage by boostrap
	    CAT_TO_DELETE.slug = c_d.dataset.slug;
	    CAT_TO_DELETE.html = c_d.parentNode.parentNode;
	});

    }

    // Handler to edit category, c_e=current category to edit
    let editHandler = (c_e) =>{
	c_e.addEventListener('click', (e) =>{
	    cat_edit_title = c_e.dataset.title.trim();
	    cat_edit_slug = c_e.dataset.slug.trim();
	    cat_input.value = cat_edit_title;;
	    modal_title.innerText = c_e.getAttribute('title').trim(); 
	    window.setTimeout(function(){ cat_input.focus()}, 500) // focus in input (category title)

	    // add videos of the current category into the dialog
	    saveCatBtn.setAttribute("data-action", "edit");
	    saveCatBtn.innerText = gettext("Save category");
	    let jsonData = getSavedData(cat_edit_slug);
	    CURR_CATEGORY = jsonData;
	    DOMCurrentEditCat = c_e.parentNode.parentNode;
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
	})
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
        editHandler(c_e);
    });

    // listener on close modal btn
    let closeBtn = document.querySelector(".modal-footer #cancelDialog");
    closeBtn.addEventListener('click', (e) =>{ window.setTimeout(function(){refreshDialog();}, 50) });
    let closeCrossBtn = document.querySelector("#manageCategoryModal .modal-header .close") || document.querySelector("#manageCategoryModal .modal-header button");
    console.log(closeCrossBtn)
    closeCrossBtn.addEventListener('click', (e) =>{
	if(e.target.getAttribute("class") === "close" || e.target.parentNode.classList.contains('close'))
	    window.setTimeout(function(){refreshDialog();}, 50)
    });
    let modalContainer = document.querySelector("#manageCategoryModal");
    modalContainer.addEventListener('click', (e) =>{
	if(e.target.getAttribute('id') === "manageCategoryModal")
	    window.setTimeout(function(){refreshDialog();}, 50)
    });
    
    // Add onclick event to delete a category
    let cats_del = document.querySelectorAll("#my_videos_filter .categories_list_item #remove_category_icon");
    cats_del.forEach(c_d => {
	deleteHandler(c_d);
    });

    // Add onclick event to delete a category
    let del_cat = document.querySelector("#confirm_remove_category_btn");
    del_cat.addEventListener('click', (e) =>{
        if(CAT_TO_DELETE.slug && CAT_TO_DELETE.html)
	{
	    // Delete category
	    let cat = findCategory(CAT_TO_DELETE.slug);
	    
	    if(Object.keys(cat).length)
	    {
		fetch(`${BASE_URL}delete/${cat.id}/`, {
		    method: "POST",
		    headers: HEADERS
	    	}).then(response =>{
		    response.json().then(data =>{
			console.log(data);
			deleteFromSavedData(CAT_TO_DELETE.slug);
			document.querySelector("#my_videos_filter .categories_list").removeChild(CAT_TO_DELETE.html);
			delete CAT_TO_DELETE.slug;
			delete CAT_TO_DELETE.html;
			// close modal
			document.querySelector("#deleteCategoryModal .modal-footer .close_modal").click();
		    });
		});
	        // Ajax request to delete category
	    }
	    else
	    {
		//TODO display msg error cat 
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
	let postData = {
	    title:  cat_input.value.trim(),
	    videos: videos
	};
	if(cat_input.value.trim() === "")
        {
	    // TODO display errors msg
            return;	    
	}
        if(Object.keys(CURR_CATEGORY).length > 0 && DOMCurrentEditCat) // Editing mode
        {
	    // Update new data, server side
    	    postCategoryData(`${BASE_URL}edit/${CURR_CATEGORY.slug}/`, postData).then(data =>{
		// Update new data, client side
	        deleteFromSavedData(CURR_CATEGORY.slug);
		saveCategoryData(data);
		DOMCurrentEditCat.querySelector('.cat_title').textContent = data.title
		DOMCurrentEditCat.querySelectorAll('span').forEach(sp => sp.setAttribute('data-slug', data.slug));
		DOMCurrentEditCat = null
		CURR_CATEGORY = {};
		// close modal
	    	document.querySelector("#manageCategoryModal #cancelDialog").click()
		refreshDialog();
	    }).catch(err =>{
	        console.log(err);
	    });
	}
	else // Adding mode
	{
    	    postCategoryData(`${BASE_URL}add/`, postData).then(data =>{

    		let li =  getCategoryLi(data.title, data.slug);
		document.querySelector("#my_videos_filter .categories_list").appendChild(li);
	    });
	    document.querySelector("#manageCategoryModal #cancelDialog").click()
	    refreshDialog();
	    console.log("ADDING MODE")
	}

    });

    // Add onclick event to add a new category
    let add_cat = document.querySelector('#my_videos_filter #add_category_btn');
    add_cat.addEventListener('click', e=>{
        modal_title.innerText = add_cat.getAttribute('title').trim(); 
        cat_input.value = "";
        // set Save button text to 'create category'
        saveCatBtn.textContent = gettext("Create category");
        saveCatBtn.setAttribute("data-action", "create");
        CURR_CATEGORY = {};
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
	    e.stopPropagation();
            c.parentNode.parentNode.querySelectorAll(".categories_list_item").forEach(c_p =>{
	        c_p.classList.remove("active");
	    });
	    c.parentNode.classList.toggle("active");
	    let cat_filter_slug = c.dataset.slug;
	    fetch(`${BASE_URL}${cat_filter_slug}/`, {headers: HEADERS}).then(response =>{
	        response.json().then(data=>{
	            console.log(data);
		});
	    });
	});
    });
})( JSON.parse(JSON.stringify(CATEGORIES_DATA)) );
