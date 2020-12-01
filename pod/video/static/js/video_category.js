(function(CATEGORIES_DATA){
    const SERVER_DATA = CATEGORIES_DATA.filter(c => !Number.isInteger(c))
    // Category to delete
    const CAT_TO_DELETE = {
	html: undefined,
	id: undefined,
	slug: undefined,
    }
    const BASE_URL = `${window.location.origin}${window.location.pathname}categories/`;
    const EDIT_URL = `${window.location.origin}/video_edit/`;
    const COMPLETION_URL = `${window.location.origin}/video_completion/`;
    const CHAPTER_URL = `${window.location.origin}/video_chapter/`;
    const DELETE_URL = `${window.location.origin}/video_delete/`;
    const VIDEO_URL = `${window.location.origin}/video/`;
    const VIDEOS_LIST_CHUNK = {
        videos: {
	    chunk: [], // all videos chunked
	    selected: [], // current selected videos
	    unselected: [] // current unselected videos
	}, // all videos
	page_index: 0, // current index
	size: 12 // number videos per view
    };
    const modal_video_list = document.querySelector('.category_modal_videos_list');
    let videos_list = document.querySelector("#videos_list.infinite-container:not(.filtered)");
    let saveCatBtn = document.querySelector("#manageCategoryModal #saveCategory" ); // btn in dialog
    let modal_title = document.querySelector("#manageCategoryModal #modal_title");
    let cat_input = document.querySelector("#manageCategoryModal #catTitle");
    let CURR_CATEGORY = {}; // current editing category (js object)
    let DOMCurrentEditCat = null; // current editing category (html DOM)
    // show loader 
    let loader = document.querySelector(".loader_wrapper");

    const SAVED_DATA = {}; // To prevent too many requests to the server
    const CURR_FILTER = {slug: null, id: null} // the category currently filtering 
    const HEADERS = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": Cookies.get("csrftoken"),
        "Accept": "application/json"
    }
   
    // show paginate video
    const show_paginate_videos = (paginator=true)=>
    {
        if(paginator) modal_video_list.classList.add("show");
	const html_paginator = modal_video_list.querySelector('.paginator');
	modal_video_list.innerHTML = '';
	modal_video_list.appendChild(html_paginator);
	let videos_to_display = VIDEOS_LIST_CHUNK.videos.chunk.length?VIDEOS_LIST_CHUNK.videos.chunk[VIDEOS_LIST_CHUNK.page_index]:[];
        videos_to_display.forEach(v => appendVideoCard(
	    toggleSelectedClass(v)
	));
    }
    // Chunk array
    const chunk = (arr, size) => Array.from({length: Math.ceil(arr.length/size)}, (v,i) => arr.slice(i*size, i*size+size));
    const paginate = (cat_videos) => {
	VIDEOS_LIST_CHUNK.page_index = 0;
	prev.classList.add("disable");
	const video_elements = Array.from(modal_video_list.querySelectorAll(".category_modal_videos_list .infinite-item"));
	VIDEOS_LIST_CHUNK.videos.selected = cat_videos.map( v => getModalVideoCard(v));

	// Saving unselected videos
	if(video_elements.length && !VIDEOS_LIST_CHUNK.videos.unselected.length)
	{
	    VIDEOS_LIST_CHUNK.videos.unselected = video_elements.filter(html_v => !html_v.classList.contains('selected'));
	}
	VIDEOS_LIST_CHUNK.videos.chunk = chunk([...VIDEOS_LIST_CHUNK.videos.unselected, ...VIDEOS_LIST_CHUNK.videos.selected], VIDEOS_LIST_CHUNK.size);
	pages_info.innerText = `${VIDEOS_LIST_CHUNK.page_index+1}/${VIDEOS_LIST_CHUNK.videos.chunk.length}`;
	pages_info.setAttribute('title', `${VIDEOS_LIST_CHUNK.page_index+1}/${VIDEOS_LIST_CHUNK.videos.chunk.length}`);
	if(VIDEOS_LIST_CHUNK.videos.chunk.length > 1)
        {
            modal_video_list.classList.add("show");
	    modal_video_list.querySelector('.next_content').classList.remove('disable');
	    show_paginate_videos();
	}
	else
	{
	    show_paginate_videos(false);
            modal_video_list.classList.remove("show");
	}
    }

    // Add event to paginate
    let pages_info = document.querySelector('.paginator .pages_infos');
    let next = document.querySelector('.paginator .next_content');
    let prev = document.querySelector('.paginator .previous_content');
    prev.addEventListener('click', e => {
        e.preventDefault();
	e.stopPropagation();
        VIDEOS_LIST_CHUNK.page_index -= VIDEOS_LIST_CHUNK.page_index>0? 1 : 0;
	let nbr_pages = VIDEOS_LIST_CHUNK.videos.chunk.length-1;
	if(VIDEOS_LIST_CHUNK.page_index === 0)
	    prev.setAttribute('class', 'previous_content disable');
        next.classList.remove('disable');
	pages_info.innerText = `${VIDEOS_LIST_CHUNK.page_index+1}/${nbr_pages+1}`;
	pages_info.setAttribute('title', `${VIDEOS_LIST_CHUNK.page_index+1}/${nbr_pages+1}`);
        show_paginate_videos();
    });
    next.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
	let nbr_pages = VIDEOS_LIST_CHUNK.videos.chunk.length-1;
        VIDEOS_LIST_CHUNK.page_index += VIDEOS_LIST_CHUNK.page_index< nbr_pages? 1 : 0;
	if(VIDEOS_LIST_CHUNK.page_index === nbr_pages)
            next.setAttribute('class', 'next_content disable');

	prev.classList.remove('disable');
	pages_info.innerText = `${VIDEOS_LIST_CHUNK.page_index+1}/${nbr_pages+1}`;
	pages_info.setAttribute('title', `${VIDEOS_LIST_CHUNK.page_index+1}/${nbr_pages+1}`);
	show_paginate_videos();
    });

    // Search categery
    let searchCatInput = document.querySelector("#my_videos_filter #searchcategories");
    let searchCatHandler = (s) =>{
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
	searchCatHandler(searchCatInput.value.trim());
    });
   
    // Update text 'Number video found' on filtering
    let manageNumberVideoFoundText = (v_len) =>{
        let text = (v_len>1)?gettext('videos found'):gettext('video found');
	let h3 =  document.querySelector(".jumbotron h3");
        h3.textContent = `${v_len} ${text}`;
	if(!v_len)
        {
	    text = gettext("Sorry, no video found");
            getVideosFilteredContainer().innerHTML = `<p class="alert-warning">${text}</p>`;
	}
	else
        {
            // delete warning text videos found
            let warning = document.querySelector('#videos_list.filtered .alert-warning');
            if(warning) warning.parentNode.removeChild(warning);
	}

    }

    // Add/Remove active class on category, html_el = <li></li>
    let manageCssActiveClass = (html_el)=>{
	html_el.parentNode.querySelectorAll(".categories_list_item").forEach(c_p =>{
	        c_p.classList.remove("active");
	});
	let curr_slug = html_el.querySelector(".cat_title").dataset.slug;
	let curr_id = html_el.querySelector("#remove_category_icon").dataset.del;
	html_el.classList.toggle('active');
        getVideosFilteredContainer().innerHTML = '';
	if(CURR_FILTER.slug === curr_slug && CURR_FILTER.id == curr_id)
	{
            html_el.classList.remove('active');// unfilter
	    CURR_FILTER.slug = null;
	    CURR_FILTER.id = null;
	    videos_list.setAttribute('class', 'row infinite-container');
            getVideosFilteredContainer().classList.add('hidden');
	    let more_btn = videos_list.parentNode.querySelector(".infinite-more-link");
	    if(more_btn)
	        more_btn.setAttribute('class', 'infinite-more-link');
	}
	else // filter
	{
            html_el.classList.add('active');
            let {id, slug} = findCategory(curr_slug, curr_id);
            CURR_FILTER.id = id;
	    CURR_FILTER.slug = slug;
	    
            getVideosFilteredContainer().classList.remove('hidden');

	    if(videos_list){
	        videos_list.setAttribute('class', 'row infinite-container hidden');
	        let more_btn = videos_list.parentNode.querySelector(".infinite-more-link");
	        if(more_btn)
	            more_btn.setAttribute('class', 'infinite-more-link hidden');
	    }
	}
    }
	
    // Create filtered videos container (HtmlELement)
    let getVideosFilteredContainer = () =>{
	let videos_list_filtered = document.querySelector(".jumbotron .filtered.infinite-container");
	if(videos_list_filtered){
	    return videos_list_filtered;
	}
	videos_list_filtered = document.createElement('div');
	videos_list_filtered.setAttribute('class', 'filtered infinite-container row');
	videos_list_filtered.setAttribute('id', 'videos_list');
	document.querySelector(".jumbotron").appendChild(videos_list_filtered);
	return videos_list_filtered;
    }
    // Update videos Filtered in filtered container after editing category
    let updateFilteredVideosContainer = (category_data) =>{
	if(CURR_FILTER.slug && CURR_FILTER.id && CURR_CATEGORY.slug === CURR_FILTER.slug && CURR_CATEGORY.id === CURR_FILTER.id)
        {
	    let actual_videos = VIDEOS_LIST_CHUNK.videos.selected.map(v_html => v_html.dataset.slug);
	    let old_videos = getSavedData(CURR_FILTER.id).videos.map(v => v.slug);
	    let rm = old_videos.filter( v => !actual_videos.includes(v) );
	    let added = actual_videos.filter( v=> !old_videos.includes(v));
	    let container_filtered = getVideosFilteredContainer();

	    let maxLen = rm.length > added.length? rm.length: added.length;
	    for(let i=0; i < maxLen; i++)
            {
                // remove video that was deselected when editing category
		if(rm[i])
	        {
		    container_filtered.removeChild(
		        container_filtered.querySelector(`.infinite-item[data-slug="${rm[i]}"`));
		}

		// Add video that was selected when editing category
		if(added[i])
		{
		    container_filtered.appendChild(
		        getVideoElement(
			    category_data.videos.find( v=> v.slug === added[i])
			)
		    );
		}
            }
            manageNumberVideoFoundText(actual_videos.length);
	}
	

    }
    // Add click event to manage filter video on click category
    let manageFilterVideos = (c)=>{
        c.addEventListener('click', e =>{
	    e.stopPropagation();
	    loader.classList.add('show');
	    let cat_filter_slug = c.dataset.slug.trim();
	    let cat_filter_id = c.parentNode.querySelector('.category_actions #remove_category_icon').dataset.del.trim();
	    videos_list_filtered = getVideosFilteredContainer(); 
	    manageCssActiveClass(c.parentNode); // manage active css class
	    let jsonData = getSavedData(cat_filter_id);
	    if( Object.keys(jsonData).length )
	    {
		let videos_nb = (!CURR_FILTER.slug && !CURR_FILTER.id)?CATEGORIES_DATA[0]:jsonData.videos.length; 
	        manageNumberVideoFoundText(videos_nb); // update text 'video found'
	        loader.classList.remove('show');
		if(CURR_FILTER.slug && CURR_FILTER.id)
                jsonData.videos.forEach(v=>{
                    videos_list_filtered.appendChild(
		        getVideoElement(v)
		    );
		});
	    }
	    else
	    {
	        jsonData = fetchCategoryData(cat_filter_slug);
	        jsonData.then( data =>{
    		    manageNumberVideoFoundText(data.videos.length); // update text 'video found'
		    if(CURR_FILTER.slug && CURR_FILTER.id)
		    data.videos.forEach(v=>{
		        videos_list_filtered.appendChild(
			    getVideoElement(v)
		        );
		    });
		    // save data
		    saveCategoryData(data);
	            loader.classList.remove('show');
		});
	    }
	});
    }

    // remove all current selected videos in dialog
    let refreshDialog = () =>{
	
	let videos = document.querySelectorAll(".category_modal_videos_list .selected");
	videos.forEach(v =>{ v.parentNode.removeChild(v) });
    }

    // Save/update category data locally
    let saveCategoryData = (data)=>{
        SAVED_DATA[`${data.id}`] = data;
    }

    // Delete category data locally
    let deleteFromSavedData = (c_slug)=>{
        if(Object.keys(SAVED_DATA).includes(c_slug))
            delete SAVED_DATA[id];
    }
    
    // Search cat by slug
    let findCategory = (slug, id=0) =>{
	let cat = SERVER_DATA.find(c => (c.slug === slug && c.id == id))
	if(!cat)
	    cat = getSavedData(id=id);
	return cat;
    }

    // Get saved category data
    let getSavedData = (id) =>{
	let cat = {}
	if(Object.keys(SAVED_DATA).includes(id.toString(10)))
            cat = SAVED_DATA[id.toString(10)];

	return cat;
    }

    // Add event toggle selected class on el
    let toggleSelectedClass = (el)=>{
	if(el.dataset.hasevent != "true")
        {
            el.addEventListener('click', e=>{
	        e.preventDefault();
	        e.stopPropagation();
	        el.classList.toggle("selected");
	        let selected = el.classList.contains('selected');
	        if(selected)
	        {
	            VIDEOS_LIST_CHUNK.videos.unselected = VIDEOS_LIST_CHUNK.videos.unselected.filter(v => !v.classList.contains('selected'));
	            VIDEOS_LIST_CHUNK.videos.selected = [...VIDEOS_LIST_CHUNK.videos.selected, el];
	        }
	        else
	        {
	            VIDEOS_LIST_CHUNK.videos.selected = VIDEOS_LIST_CHUNK.videos.selected.filter(v => v.classList.contains('selected'));
	            VIDEOS_LIST_CHUNK.videos.unselected = [...VIDEOS_LIST_CHUNK.videos.unselected, el];
	        }
	    });
	    el.setAttribute('data-hasevent', true);
	}
        return el;	
    }

    // Make requets => get category data
    let fetchCategoryData = async (cat_slug) =>{
        try
	{
	    let resp = await fetch(`${BASE_URL}${cat_slug}/`,{headers: HEADERS});
	    return await resp.json();
	} 
	catch(e) {
	    loader.classList.remove('show');
	    showAlertMessage(gettext('An error occured, please refresh the page and try again.'), "error", delay=10000);
	    console.error(e);
	}
    }

    // Make post request. for edit or add category, postData(object)
    let postCategoryData = async (url, postData) =>{
	try
	{
            let resp = await fetch(url, {method: "POST", body: JSON.stringify(postData), headers: HEADERS});
	    return await resp.json();
        }
	catch(e){
	    loader.classList.remove('show');
	    showAlertMessage(gettext('An error occured, please refresh the page and try again.</br>You cannot add two categories with the same title.'), "error", delay=10000);
	    console.error(e);
	}
    }

    let get_type_icon = (is_video=true)=>{
        let videoContent_Text = gettext("Video content.");
	let audioContent_Text = gettext("Audio content.");
	if(is_video)
	    return `<span title="${videoContent_Text}">
		        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-film align-bottom"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line><line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line><line x1="17" y1="7" x2="22" y2="7"></line></svg>
		    </span>`;
	return `<span title="${audioContent_Text}">
		    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-radio"><circle cx="12" cy="12" r="2"></circle><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"></path></svg>
		</span>`;
    }
    
    // Create category html element <li></li>
    let getCategoryLi = (title, slug, id) =>{
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
	editHandler(spanEdit); // append edit click event

        let spanDelete = document.createElement('span');
	spanDelete.setAttribute('title', gettext("Delete the category"));
	spanDelete.setAttribute('data-toggle', 'modal');
	spanDelete.setAttribute('data-target', '#deleteCategoryModal');
	spanDelete.setAttribute('data-del', id);
	spanDelete.setAttribute('data-slug', slug);
	spanDelete.setAttribute('data-title', title);
	spanDelete.setAttribute('class', 'remove_category');
	spanDelete.setAttribute('id', 'remove_category_icon');
	spanDelete.innerHTML = `
	    <svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="trash-alt" class="svg-inline--fa fa-trash-alt fa-w-14" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="currentColor" d="M32 464a48 48 0 0 0 48 48h288a48 48 0 0 0 48-48V128H32zm272-256a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zm-96 0a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zm-96 0a16 16 0 0 1 32 0v224a16 16 0 0 1-32 0zM432 32H312l-9.4-18.7A24 24 0 0 0 281.1 0H166.8a23.72 23.72 0 0 0-21.4 13.3L136 32H16A16 16 0 0 0 0 48v32a16 16 0 0 0 16 16h416a16 16 0 0 0 16-16V48a16 16 0 0 0-16-16z"></path></svg>
	`;
	deleteHandler(spanDelete); // append detele click event

	let li = document.createElement('li');
	li.setAttribute("class", "categories_list_item");
	li.innerHTML = `
	    <div class="category_actions"></div>`;

	let catTitleHtml = document.createElement('span');
	catTitleHtml.setAttribute('class', 'cat_title');
	catTitleHtml.setAttribute('title', title);
	catTitleHtml.setAttribute('data-slug', slug)
	catTitleHtml.innerText = title;
    	manageFilterVideos(catTitleHtml); // append filter click event
	li.prepend(catTitleHtml);
	li.querySelector(".category_actions").appendChild(spanEdit);
	li.querySelector(".category_actions").appendChild(spanDelete);
	return li;
    }

    // Create video html element card for Category Dialog
    let createHtmlVideoCard = (v)=>{
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

    // Create video video html element for my_videos (on filtering with category)
    // video = object
    let getVideoElement = (video) =>{
	let span_info = `
	    <span>
	`;
	let has_password = () =>{
	    let span = ``;
	    let title = gettext('This content is password protected.');
	    if(video.has_password)
	    {
		span = `<span title="${title}"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-lock align-bottom"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></span>`;
	    }
	    return span;
	}
	let has_chapter = () =>{
	    let span = ``;
	    let title = gettext('This content is chaptered.');
	    if(video.has_chapter)
	    {
		span = `<span title="${title}"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-list align-bottom"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3" y2="6"></line><line x1="3" y1="12" x2="3" y2="12"></line><line x1="3" y1="18" x2="3" y2="18"></line></svg></span>`;
	    }
	    return span;
	}
	let is_draft = () =>{
	    let span = ``;
	    let title = gettext('This content is in draft.');
	    if(video.is_draft)
	    {
		span = `<span title="${title}">
			    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-x-circle align-bottom"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg></span>`;
	    }
	    return span;
	}
	let is_video = () =>{
	    let span = ``;
	    let title = gettext('Video content.');
	    if(video.is_video)
	    {
		span = `<span title="${title}">
			    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-film align-bottom"><rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18"></rect><line x1="7" y1="2" x2="7" y2="22"></line><line x1="17" y1="2" x2="17" y2="22"></line><line x1="2" y1="12" x2="22" y2="12"></line><line x1="2" y1="7" x2="7" y2="7"></line><line x1="2" y1="17" x2="7" y2="17"></line><line x1="17" y1="17" x2="22" y2="17"></line><line x1="17" y1="7" x2="22" y2="7"></line></svg></span>`;
	    }
	    else
	    {
	    	title = gettext('Audio content.');
		span = `<span title="${title}"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-radio"><circle cx="12" cy="12" r="2"></circle><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"></path></svg></i></span>`;
	    }
	    return span;
	}
	let edit_text = gettext('Edit the video');
	let completion_text = gettext('Complete the video');
	let chapter_text = gettext('Chapter the video');
	let delete_text = gettext('Delete the video');
	let infinite_item = document.createElement('div');
	infinite_item.setAttribute('class', 'infinite-item col-12 col-md-6 col-lg-3 mb-2 card-group');
	infinite_item.setAttribute('data-slug', video.slug);
	let card = document.createElement('div');
	card.setAttribute('class', 'card mb-4 box-shadow border-secondary video-car');
	card.innerHTML = `
            <div class="card-header">
	        <div class="d-flex justify-content-between align-items-center">
	            <small class="text-muted time">${video.duration}</small>
	            <span class="text-muted small">
		        ${has_password()}
			${is_draft()}
			${has_chapter()}
			${is_video()}
	            </span>
	        </div>
	    </div>
            <div class="d-flex align_items-center">
                <a class="link-center-pod" href="${VIDEO_URL}${video.slug}" title="${video.title}">
		    ${video.thumbnail}
	        </a>
            </div>
	    <div class="card-body">
                <footer class="card-footer card-footer-pod p-0 m-0">
		    <a href="${EDIT_URL}${video.slug}" title="${edit_text}" class="p-0 m-0 btn btn-light btn-sm pl-1">
		        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-edit align-bottom"><path d="M20 14.66V20a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h5.34"></path><polygon points="18 2 22 6 12 16 8 16 8 12 18 2"></polygon></svg>
		    </a>
		    <a href="${COMPLETION_URL}${video.slug}" title="${completion_text}" class="p-0 m-0 btn btn-light btn-sm pl-1">
		        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-file-text align-bottom"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
		    <a href="${CHAPTER_URL}${video.slug}" title="${chapter_text}" class="p-0 m-0 btn btn-light btn-sm pl-1">
			<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-list align-bottom"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3" y2="6"></line><line x1="3" y1="12" x2="3" y2="12"></line><line x1="3" y1="18" x2="3" y2="18"></line></svg>
		    </a>
		    <a href="${DELETE_URL}${video.slug}" title="${delete_text}" class="p-0 m-0 btn btn-light btn-sm pl-1">
		        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-trash-2 align-bottom"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
		    </a>
                </footer>
		<span class="small video-title">
                    <a href="${VIDEO_URL}${video.slug}" title="${video.title}">${video.title}</a>
		</span>
	    </div>
	`;
	infinite_item.appendChild(card);
	return infinite_item;
    }

    // Create alert message
    let showAlertMessage = (message, type="success", delay=4000) => {
	let title = type.charAt(0).toUpperCase() + type.slice(1);
	let icon = type==="success"?`<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-check-circle"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>`: type==="error"? `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-alert-triangle"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-info"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
        let alert_message = document.createElement("div");
	alert_message.setAttribute('class', `category_alert alert_${type}`);
	alert_message.innerHTML = `<div class="alert_content"><span class="alert_icon">${icon}</span><span class="alert_title">${title}</span><span class="alert_text">${message}</span>`;
	document.body.appendChild(alert_message);
	window.setTimeout(() => alert_message.classList.add('show'), 1000)
	window.setTimeout( () =>{
	    alert_message.classList.add('hide');
	    window.setTimeout(()=> document.body.removeChild(alert_message), 1000);
	}, delay);
    }

    // Handler to edit category, c_e=current category to edit
    let editHandler = (c_e) =>{
	c_e.addEventListener('click', (e) =>
	{
	    loader.classList.add('show');
	    cat_edit_title = c_e.dataset.title.trim();
	    cat_edit_slug = c_e.dataset.slug.trim();
	    cat_edit_id = c_e.parentNode.querySelector("#remove_category_icon").dataset.del.trim();
	    cat_input.value = cat_edit_title;;
	    modal_title.innerText = c_e.getAttribute('title').trim(); 
	    window.setTimeout(function(){ cat_input.focus()}, 500) // focus in input (category title)

	    // add videos of the current category into the dialog
	    saveCatBtn.setAttribute("data-action", "edit");
	    saveCatBtn.innerText = gettext("Save category");
	    let jsonData = getSavedData(cat_edit_id);
	    CURR_CATEGORY = jsonData;
	    DOMCurrentEditCat = c_e.parentNode.parentNode;
	    if( Object.keys(jsonData).length )
	    {
		paginate(jsonData.videos);
		loader.classList.remove('show');
	    }
	    else
	    {
	        jsonData = fetchCategoryData(cat_edit_slug);
	        jsonData.then( data =>{

		    paginate(data.videos);

		    // save data
		    saveCategoryData(data);

		    CURR_CATEGORY = data;

		    loader.classList.remove('show');

		}).catch(e =>{
		    loader.classList.remove('show');
		    showAlertMessage(gettext('An error occured, please refresh the page and try again.'), "error", delay=10000);
		    console.error(e)
		});
	    }
	});
    }

    // get modal video card
    let getModalVideoCard = (v, selected=true) => {
	let videoCard = createHtmlVideoCard(v);
	let v_wrapper = document.createElement("Div");
	v_wrapper.setAttribute("data-slug", v.slug);
	let selectClass = selected? 'selected':'';
	v_wrapper.setAttribute("class", "infinite-item col-12 col-md-6 col-lg-3 mb-2 card-group "+selectClass)
        v_wrapper.innerHTML = videoCard;
	return v_wrapper;
    }
    // Append video card in category modal
    let appendVideoCard = (v)=>{
	let modalListVideo = document.querySelector("#manageCategoryModal .category_modal_videos_list");
	modalListVideo.insertBefore(v, modalListVideo.querySelector(".paginator"));
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
    closeCrossBtn.addEventListener('click', (e) =>{
	if(e.target.getAttribute("class") === "close" || e.target.parentNode.classList.contains('close'))
	    window.setTimeout(function(){refreshDialog();}, 50)
    });
    let modalContainer = document.querySelector("#manageCategoryModal");
    modalContainer.addEventListener('click', (e) =>{
	if(e.target.getAttribute('id') === "manageCategoryModal")
	    window.setTimeout(function(){refreshDialog();}, 50)
    });

    // Handler to delete category, c_d=current category to delete
    // Temporarily save the category to delete
    let deleteHandler = (c_d) =>{
	c_d.addEventListener('click', (e) =>{
 	    // Show confirm modal => manage by boostrap
	    CAT_TO_DELETE.html = c_d.parentNode.parentNode;
	    CAT_TO_DELETE.id = c_d.dataset.del;
	    CAT_TO_DELETE.slug = c_d.dataset.slug;
	});

    }

    // Add onclick event to delete a category
    let cats_del = document.querySelectorAll("#my_videos_filter .categories_list_item #remove_category_icon");
    cats_del.forEach(c_d => {
	deleteHandler(c_d);
    });

    // Add onclick event to delete a category
    let del_cat = document.querySelector("#confirm_remove_category_btn");
    del_cat.addEventListener('click', (e) =>{
	loader.classList.add('show');
        if(CAT_TO_DELETE.slug && CAT_TO_DELETE.id && CAT_TO_DELETE.html)
	{
	    // Delete category
	    let cat = findCategory(slug=CAT_TO_DELETE.slug, id=CAT_TO_DELETE.id);
	    if(Object.keys(cat).length)
	    {
		fetch(`${BASE_URL}delete/${cat.id}/`, {
		    method: "POST",
		    headers: HEADERS
	    	}).then(response =>{
		    response.json().then(data =>{
			showAlertMessage(gettext('Category deleted successfully'));
			deleteFromSavedData(cat.slug); // delete from local save
			data.videos.forEach(v =>{ // append all the videos into chunk videos unselected
			    VIDEOS_LIST_CHUNK.videos.unselected = [
				...VIDEOS_LIST_CHUNK.videos.unselected, getModalVideoCard(v, false)]
			});
			document.querySelector("#my_videos_filter .categories_list").removeChild(CAT_TO_DELETE.html);
			let filtered_container = getVideosFilteredContainer();
			if(filtered_container && CAT_TO_DELETE.id == CURR_FILTER.id && CAT_TO_DELETE.slug === CURR_FILTER.slug)
			{
		            filtered_container.parentNode.removeChild(filtered_container);
			    let my_videos_container = document.querySelector(".infinite-container.hidden")
			    if(my_videos_container) my_videos_container.classList.remove('hidden');
                            manageNumberVideoFoundText(CATEGORIES_DATA[0]);
			    CURR_FILTER.slug = null;
			    CURR_FILTER.id = null;
			    document.querySelectorAll(".categories_list .categories_list_item").forEach(c => c.classList.remove('active'));
			}
			delete CAT_TO_DELETE.html;
			delete CAT_TO_DELETE.id;
			delete CAT_TO_DELETE.slug;
			loader.classList.remove('show');
			// close modal
			document.querySelector("#deleteCategoryModal .modal-footer .close_modal").click();
		    });
		});
	    }
	    else
	    {
		//TODO display msg error cat 
		loader.classList.remove('show');
	    }
	}
	else
	{ 
	    // display msg error like 'no category to delete'
	    loader.classList.remove('show');
	}
    });


    // Add onclick event to save category (create or edit) data
    saveCatBtn.addEventListener("click", e=>{
        e.preventDefault()
        e.stopPropagation()

	loader.classList.add("show");

        //let videos = Array.from(document.querySelectorAll(".category_modal_videos_list .selected")).map(v_el => v_el.dataset.slug.trim());
	const videos = VIDEOS_LIST_CHUNK.videos.selected.map(html_v => html_v.dataset.slug);
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
    		updateFilteredVideosContainer(data); // update filered videos in filtered container
	        deleteFromSavedData(CURR_CATEGORY.slug);
		saveCategoryData(data);
		DOMCurrentEditCat.querySelector('.cat_title').textContent = data.title;
		DOMCurrentEditCat.querySelector('.cat_title').setAttribute('title', data.title);
		DOMCurrentEditCat.querySelectorAll('span').forEach(sp => {sp.setAttribute('data-slug', data.slug); sp.setAttribute('data-title', data.title)});
		DOMCurrentEditCat = null
		CURR_CATEGORY = {};
		// close modal
	    	document.querySelector("#manageCategoryModal #cancelDialog").click()
		refreshDialog();
                showAlertMessage(gettext('Category changes saved successfully'));
		loader.classList.remove("show"); // hide loader
	    }).catch(err =>{
		loader.classList.remove('show');
		showAlertMessage(gettext('An error occured, please refresh the page and try again.'), "error", delay=10000);
	        console.log(err);
	    });
	}
	else // Adding mode
	{
    	    postCategoryData(`${BASE_URL}add/`, postData).then(data =>{
    		let li =  getCategoryLi(data.category.title, data.category.slug, data.category.id);
		document.querySelector("#my_videos_filter .categories_list").appendChild(li);
                showAlertMessage(gettext('Category created successfully'));
		saveCategoryData(data.category); // saving cat localy to prevent more request to the server
		loader.classList.remove("show"); // hide loader
	    });
	    document.querySelector("#manageCategoryModal #cancelDialog").click()
	    refreshDialog();
	}

    });

    // Add onclick event to add a new category
    let add_cat = document.querySelector('#my_videos_filter #add_category_btn');
    add_cat.addEventListener('click', e=>{
	paginate([]);
        modal_title.innerText = add_cat.getAttribute('title').trim(); 
        cat_input.value = "";
        // Change the Save button text to 'create category'
        saveCatBtn.textContent = gettext("Create category");
        saveCatBtn.setAttribute("data-action", "create");
        CURR_CATEGORY = {};
        window.setTimeout(function(){ cat_input.focus()}, 500)
    });

    // Add click event on category in filter bar to filter videos in my_videos vue
    let cats = document.querySelectorAll("#my_videos_filter .categories_list_item .cat_title");
    cats.forEach(c =>{
    	manageFilterVideos(c);
    });
})( JSON.parse(JSON.stringify(CATEGORIES_DATA)) );
