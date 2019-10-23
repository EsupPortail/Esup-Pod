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
            if( !v.querySelector("label").textContent.toLowerCase().includes(search.value.toLowerCase()))
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

search.addEventListener("keyup", function(){
    filter_videos();
});
docReady(function(){
    filter_videos();
});
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

let videos_to_display = function(given_login)
{
    let videos = {};
    for(let [login, video] of Object.entries(data))
    {
        if( login.toLowerCase().includes(given_login.value.toLowerCase()))
        {
            videos[login] = video;
        }
    }
    return videos;
}

// display all her videos by login
let display_all_videos_by_login = function(given_login)
{
    // Make a request to get all user videos in BD
    if( given_login.value.length >= 3 )
    {
        clean_videos();
        let videos_display = videos_to_display(given_login);
        if( Object.keys(videos_display).length === 0 ) remove_select_all_videos();
        // Add all her videos to the views
        for(let [login, user_videos] of Object.entries(videos_display))
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
    else
    {
        remove_select_all_videos();
        list_videos.querySelectorAll('.form-group .list_videos__data').forEach(function(v1)
        {
            list_videos.removeChild(v1);
        });
    }
}
// listening to oldlogin to display all her videos
oldlogin.addEventListener("keyup", function()
{
    display_all_videos_by_login(this)
});
docReady(display_all_videos_by_login(oldlogin));


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
    let old_owner = oldlogin.value;
    let new_owner = newlogin.value;

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
