let check_all_videos = document.querySelector('#all_videos');
let oldlogin = document.querySelector('#oldlogin');
let newlogin = document.querySelector('#newlogin');
let submit = document.querySelector("#changeownerjs");
let search = document.querySelector("#list_videos__search");
let list_videos = document.querySelector(".list_videos");
let videos = list_videos.querySelectorAll('.form-group.list_videos__data');
let token = document.querySelector("input[name='csrfmiddlewaretoken']");

// Document Ready function
function docReady(fn) {
    // see if DOM is already available
    if (document.readyState === "complete" || document.readyState === "interactive") {
        // call on next available tick
        setTimeout(fn, 1);
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}    

// DATA FROM DATABASE
/*let data =
{
    "Jhon77":
    [
        {
            id: 1,
            title: "I'm the best in the world",
            duree: 123,
        },
        {
            id: 2,
            title: "You're my sunshine",
            duree: 103,
        },
        {
            id: 3,
            title: "Only the developper can do that",
            duree: 203,
        },{
            id: 4,
            title: "Guess what ?",
            duree: 23,
        },
    ],
    "Jean69":
    [
        {
            id: 1,
            title: "I'm the best in the world",
            duree: 123,
        },
        {
            id: 2,
            title: "You're my sunshine",
            duree: 103,
        },
        {
            id: 3,
            title: "Only the developper can do that",
            duree: 203,
        },{
            id: 4,
            title: "Guess what ?",
            duree: 23,
        },
    ],
    "Jean41":
    [
        {
            id: 1,
            title: "I'm the best in the world",
            duree: 123,
        },
        {
            id: 2,
            title: "You're my sunshine",
            duree: 103,
        },
        {
            id: 3,
            title: "Only the developper can do that",
            duree: 203,
        },{
            id: 4,
            title: "Guess what ?",
            duree: 23,
        },
    ]
}*/

let uncheck_all_video_checkbox = function()
{
    all_checkbox_are_checked = false;
    // Décoché le checkbox all_video si est coché et si un des checkbox video est décocher
    videos.forEach(function(v)
    {
        v.querySelector("input[type='checkbox']").addEventListener("change", function()
        {
            if( !this.checked)
            {
                check_all_videos.checked = false;
            }
            else
            {
                all_checkbox_are_checked = true;
            }
            // Cocher le checkbox all_video si toutes les video sont checked
            check_all_video_checkbox_if_all_video_are_checked();
        });
    });
}

docReady(uncheck_all_video_checkbox())

let uncheck_all_videos_function = function()
{
    // Décocher toutes les vidéos
    videos.forEach(function(v)
    {
        if( !v.className.includes("hidden") ) // tous séléctionner sauf ceux qui sont cachés
        {
            v.querySelector("input[type='checkbox']").checked = false;
        }
    });
}

let check_all_videos_function = function()
{
    // Cocher toutes les vidéos
    videos.forEach(function(v)
    {
        if( !v.className.includes("hidden") )
        {
            v.querySelector("input[type='checkbox']").checked = true;
        }
    });
}

function check_all_video_checkbox_if_all_video_are_checked()
{
    // Cocher le checkbox all_video si toutes les video sont checked
    checked = true;
    videos.forEach(function(v)
    {
        let vid = v.querySelector('input[type="checkbox"]');
        if(!vid.checked)
        {
            checked = false;
        }
    });
    check_all_videos.checked = checked;
}

docReady(function check_all_videos_if_all_checked_is_true()
{
    if(check_all_videos && check_all_videos.checked)
    {
        check_all_videos_function();
    }
    else
    {
        uncheck_all_videos_function();
    }
    
});

let display_all_videos = function()
{
    // Afficher toutes les vidéos
    videos.forEach(function(v)
    {
        v.classList.remove('hidden');
    });
}

let filter_videos = function()
{
    if( search.value.length >= 3 )
    {
        videos.forEach(function(v)
        {
            // si le texte tapé ne correspond pas à cette input alors on cache le input
	    // normalize("NFD").replace(/[\u0300-\u036f]/g, "") => remove accents
            if( 
		    !v
		     .querySelector("label")
		     .textContent.toLowerCase()
		     .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
		     .includes(
			    search
			     .value
			     .toLowerCase()
			     .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
		    )
	    )
            {
                v.classList.add("hidden")
            }
            else
            {
                v.classList.remove('hidden');
            }
        });
    }
    else
    {
        display_all_videos();
    }
}

search.oninput = function(){
    filter_videos();
}
// add select all videos 
let add_select_all_videos = function()
{
    /**
     * Objectif
     * <input name="all" type="checkbox" id="all_videos" >
        <label for="all_videos">Toutes les vidéos</label>
    */
    let checkbox = document.createElement('input');
    checkbox.setAttribute('name', "all");
    checkbox.setAttribute('type', "checkbox");
    checkbox.setAttribute('id', "all_videos");
    let label_checkbox = document.createElement("label");
    label_checkbox.setAttribute('for', "all_videos");
    label_checkbox.innerText = "Toutes les vidéos";

    div = document.createElement("div");
    div.setAttribute("class", "check_all_video")
   
    div.appendChild(checkbox)
    div.appendChild(label_checkbox)
    if( !list_videos.querySelector(".check_all_video") )
    {
        list_videos.querySelector(".form-group.all_video").after(div)
    }
    // Set check_all_videos variable
    check_all_videos = document.querySelector('#all_videos');
    check_all_videos.addEventListener("change", function(e)
    {
        if( this.checked)
        {
            check_all_videos_function();
        }
        else
        {
            uncheck_all_videos_function();
        }
    });
}
// Remove checkbox 'select all videos'
let remove_select_all_videos = function()
{
    if(list_videos.childElementCount > 1)
    {
        list_videos.removeChild( 
            document.querySelector(".check_all_video"));
    }
}

let clean_videos = function()
{
    if( videos.length > 0 )
    {
        videos.forEach(function(video)
        {
            if( video.parentNode)video.parentNode.removeChild(video);
        });
    }
}

let videos_to_display = function(given_login, click=false)
{
    let videos = {};
    for(let [login, user_videos] of Object.entries(data))
    {
	user_full_name = Array.isArray(user_videos)? user_videos[0].full_name : user_videos.full_name;
	user_given_login = (click)? given_login.dataset.login : given_login.value;
	if( click && login.toLowerCase() === user_given_login.toLowerCase() )
	{
		videos[login] = user_videos;
	}
	else if(!click && (login.toLowerCase().includes(user_given_login.toLowerCase()) ||
		user_full_name.toLowerCase().includes(user_given_login.toLowerCase()))
	)
        {
            videos[login] = user_videos;
        }
    }
    return videos;
}

// display all her videos by login
let display_all_videos_by_login_or_name = function(given_login, click=false)
{
    // Make a request to get all user videos in BD
    if( given_login.value.length >= 3 )
    {
        clean_videos();
        let videos_display = videos_to_display(given_login, click);
        if( Object.keys(videos_display).length === 0 ) remove_select_all_videos();
        // Add all her videos to the views
        for(let [login, user_videos] of Object.entries(videos_display))
        {
	    if( Array.isArray(user_videos) )
	    {
            	user_videos.forEach(function(v)
            	{
                	let div = document.createElement('div');
                	div.setAttribute('class', "form-group list_videos__data");
	                div.setAttribute('id', login+"-"+v.id);
			let container = document.createElement("div");
			container.setAttribute('class', 'list_videos__data_container');
			let img = document.createElement('img');
			img.setAttribute('class', 'list_videos__img');
			//img.setAttribute('target_url', v.url);
			img.setAttribute('src', v.thumbnail);
			container.addEventListener("click", function(e){
				e.preventDefault();
				window.open(v.url, '_blank');
			});
                	let input = document.createElement('input');
	                input.setAttribute('type', "checkbox");
        	        input.setAttribute('id', "video_"+v.id);
                	input.setAttribute('name', "videos[]");
	                input.setAttribute('value', v.id+"-"+login);
        	        let label = document.createElement('label');
                	label.setAttribute('for', "video_"+v.id)
	                label.innerText = v.title;
        	
        	        div.appendChild(input);
			container.appendChild(img);
			container.appendChild(label);
			div.appendChild(container);
			if( !list_videos.querySelector("#"+login+"-"+v.id) )
	                {
        	            list_videos.appendChild(div);
                	}
		});
	            add_select_all_videos();  
        	    videos = list_videos.querySelectorAll('.form-group.list_videos__data');
	            uncheck_all_video_checkbox();
	    }
        }
    }
    else
    {
        remove_select_all_videos();
        list_videos.querySelectorAll('.form-group .list_videos__data').forEach(function(v1)
        {
            list_videos.removeChild(v1);
        });
    }
}
// Add if not already added

var not_already_added = function(parentNode, child)
{
	already_added = true;
	parentNode.querySelectorAll(child.tagName).forEach(function(p)
	{
		if(p.dataset.login.toLowerCase() === child.dataset.login.toLowerCase())
		{
			already_added=false;
		}
	});
	return already_added;
}

// listening to oldlogin to display all her videos
oldlogin.oninput = function()
{
    if(oldlogin.dataset.login)
    {
	oldlogin.removeAttribute("data-login");
    }

    display_owners_suggestion(this)
    display_all_videos_by_login_or_name(this)
}
newlogin.onblur = function(e)
{
	remove_owner_suggestion_node(this, hide=true);
	e.stopPropagation();
}
oldlogin.onblur = function(e)
{
	remove_owner_suggestion_node(this, hide=true);
	e.stopPropagation();
}

newlogin.onfocus = function()
{
	if(this.parentNode.querySelector("#jsowner-list.owner-list"))
	{
		this.parentNode.querySelector(
			"#jsowner-list.owner-list").style.display = "block";
	}
}
oldlogin.onfocus = function()
{
	if(this.parentNode.querySelector("#jsowner-list.owner-list"))
	{
		this.parentNode.querySelector(
			"#jsowner-list.owner-list").style.display = "block";
	}
}

let remove_owner_suggestion_node = function(target, hide=false)
{
	let suggestionNode = target.parentNode.querySelector("#jsowner-list.owner-list");
	if(hide && suggestionNode)
	{
		suggestionNode.style.display = "none";
	}
	else if(suggestionNode)
	{
		target.parentNode.removeChild(suggestionNode);
	}
}
let display_owners_suggestion = function(given_login) 
{	
	let owner_list_element = given_login.parentNode.querySelector("#jsowner-list.owner-list");
	if( given_login.value.length >= 3 )
	{
		// Create div.owner-list if not already exists
		if( !owner_list_element )
		{
			owner_list_element = document.createElement("div");
			owner_list_element.setAttribute("id", "jsowner-list");
			owner_list_element.setAttribute("class", "owner-list");
			given_login.parentNode.appendChild(owner_list_element);
		}
		// remove all child to update owners suggestions
		owner_list_element.innerHTML = "";

        	for(let [username, user_videos] of Object.entries(data))
		{
			user_name = Array.isArray(user_videos)? user_videos[0].full_name: user_videos.full_name;
			if(user_name.trim() === "" || user_name === undefined)
			{
				user_name = username;
			}
			if( user_name.toLowerCase().includes(given_login.value.toLowerCase()) )
			{
				let p = document.createElement("p");
				p.dataset.login = username;
				p.addEventListener("mousedown", (e)=>{
					//given_login);
					//this.parentNode.previousElementSibling);
					//newlogin);
					e.stopPropagation();
					given_login.value = p.innerText;
					given_login.dataset.login = p.dataset.login;
					remove_owner_suggestion_node(given_login)
					//given_login.parentNode.removeChild(owner_list_element);
					// Update suggestions videos
					if( given_login != newlogin )
					display_all_videos_by_login_or_name(oldlogin, click=true)

				});
				// Display suggestion
				if( not_already_added(owner_list_element, p) )
				{
					p.appendChild(document.createTextNode(user_name));

					owner_list_element.appendChild(p);
				}
			}
		}
	}
	else
	{
		remove_owner_suggestion_node(given_login);
	}
}
// Display owners suggestions
newlogin.oninput = ()=>
{
	if(newlogin.dataset.login)
	{
		newlogin.removeAttribute("data-login");
	}
	display_owners_suggestion(newlogin);
}

let all_video_checkbox_checked = function()
{
    if( check_all_videos)return check_all_videos.checked;
    return false;
}

let remove_videos_changed = function()
{
    videos.forEach(function(v){
	if(v.querySelector("input[type='checkbox']").checked)
	{
	    v.parentNode.removeChild(v);
//	    v.classList.add("hidden");
	}
    });
    if( videos.length == 0){
	document.querySelector(".check_all_video").classList.add("hidden");
    }

}

let get_videos_to_change = function()
{
    let array = [];
    if( videos )
    {
        videos.forEach(function(v)
        {
            let curr_checkbox = v.querySelector("input[type='checkbox']");
            if( curr_checkbox.checked )
            {
		var tmp_label = v.querySelector("label[for='"+curr_checkbox.id+"']");
                array.push(curr_checkbox.value +"|-|" +tmp_label.textContent);
            }   
        });
    }
    return array;
}

let js_field_not_empty = function( fields )
{
    for(var i =0; i < fields.length; i++)
    {
        if(
	    (fields[i] === undefined) ||
            (typeof(fields[i]) === "string" && fields[i].trim().length === 0) ||
            (typeof(fields[i]) === "object" && fields[i].length === 0)
        ) return false;
    }
    return true;
}

let end_loading = function( callable )
{
    document.addEventListener('readystatechange', function(e){
	if(e.target.readyState === "interactive"){
	    callable();
	}
    });
	
}

let display_div_message = function(type="success", text="Les changements ont été effectués avec succès.", reload=false)
{
    /**
     * Objectif <div class="message">Les changements ont été effectués</div>
     */
    text = text.replace(/{([a-z0-9]+)}/gi,"<span class='login'>$&</span>").replace(/{|}/gi,"")
    let div = document.createElement('div');
    div.setAttribute('class', "message " + type);
    div.innerHTML = unescape(text);
	
    remove_loader();
    document.querySelector(".form-group .row").insertBefore(div, list_videos);
    setTimeout(function(){
	if(div)	div.parentNode.removeChild(div)	
    }, 2500);
}

// display success message in sessionStorage if exists
docReady(function(){

    if(sessionStorage.hasOwnProperty("success"))
    {
	display_div_message(type = "success", text=sessionStorage.getItem("success"))
	sessionStorage.removeItem("success");
    }
})

submit.addEventListener("click", function(e)
{
    e.preventDefault();
    // Add loader
    add_loader()

    let videos_to_change_owner = (all_video_checkbox_checked())? "*" : get_videos_to_change();
    let old_owner = oldlogin.dataset.login;
    let new_owner = newlogin.dataset.login;
    let success = js_field_not_empty([old_owner, new_owner, videos_to_change_owner]);
    if( success )
    {
    	let target_url= window.location.protocol+"//" + window.location.host + "/custom/update-owner/";
	let params = {
		"old_owner": old_owner,
		"new_owner": new_owner,
		"videos": videos_to_change_owner
	}
        // TODO make ajax request
        const req = new XMLHttpRequest();
        req.onload = onLoad;
	req.onloadend = onLoadEnd;

        req.open('POST', target_url);
	req.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
	req.setRequestHeader("X-CSRFToken", token.value);
        req.send(JSON.stringify(params));
    }
    else
    {
        display_div_message(type="info", text="Veuillez remplir correctement tous les champs.");
    }
})

let add_loader = function(){
	let container = document.createElement("div");
	container.setAttribute("class", "loader-container");
	let loader = document.createElement("div");
	loader.setAttribute("class", "loader-circle");
	for(var i=0; i < 4; i++){
		loader.appendChild(document.createElement("div"));
	}
	container.appendChild(loader)
	document.querySelector("body").appendChild(container)
}
let remove_loader = function()
{
	let loader = document.querySelector(".loader-container")
	if(loader) loader.parentNode.removeChild(loader);
}

/*********************************************************************************
 ******************************* AJAX ********************************************
 *********************************************************************************/
function onLoad(event) {
    // Ici, this.readyState égale XMLHttpRequest.DONE .
    if (this.status === 200 || this.status === 304) {
	document.location.reload();
	sessionStorage.setItem("success", "Les changemnts ont été effectués avec succès.")
    } else {
	display_div_message(type="error", text=this.responseText);
    }
}
function onLoadEnd(event){
	// Remove loader
	remove_loader();
}
