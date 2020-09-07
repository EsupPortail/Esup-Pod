// podfile:filewidjet.js
// select file 

if(typeof loaded == 'undefined') {
    loaded = true;
    $(document).on("click", "a.file-name", function(e) {
    if (id_input!="") {
        e.preventDefault();

        $("input#"+id_input).val($(this).data("fileid"));

        if($(this).data("filetype")=="CustomImageModel"){
            $(".btn-fileinput_"+id_input).html(gettext('Change image'));
        } else {
            $(".btn-fileinput_"+id_input).html(gettext('Change file'));
        }
        //
        //if($(".btn-fileinput_"+id_input).text().indexOf(gettext('Change file')) != -1 || $(".btn-fileinput_"+id_input).text().indexOf(gettext('Select a file')) != -1)
        //    $(".btn-fileinput_"+id_input).html(gettext('Change file'));
        //else $(".btn-fileinput_"+id_input).html(gettext('Change image'));
        //
        $("#remove_file_"+id_input).show();

        let html = "";
        if($(this).data("filetype")=="CustomImageModel"){
            html += '<img src="'+$(this).attr('href')+'" height="34" alt="'+$(this).text()+'"/>&nbsp;';
        } else {
            html += '<img style="height: 26px;vertical-align: middle;" src="'+static_url+'podfile/images/icons/default.png" alt="">&nbsp;';
        }
        html += '<strong><a href="'+$(this).attr('href')+'" target="_blank" title="'+gettext('Open file in a new tab')+'">'+$(this).text()+'</a></strong>&nbsp;';

        $("#fileinput_"+id_input).html(html);

        $("#modal-folder_"+id_input).html("");
        $('#fileModal_'+id_input).modal('hide');
    }
});

$(document).on("click", "a.folder", function(e) {
    e.preventDefault();
    var id = $(this).data("id");
    send_form_data($(this).data('target'), {}, "show_folder_files", "get");
});

$(document).on('change', "#ufile", function(e) {
    e.preventDefault();
    $("#formuploadfile").submit();
});



/****** CHANGE FILE ********/


  $(document).on("submit", "form#formchangeimage, form#formchangefile, form#formuploadfile", function (e) {
        e.preventDefault();
        //alert('FORM');
        $(this).hide();
        $(".loadingformfiles").show();
        $("#listfiles").hide();
        var data_form = new FormData($(this)[0]);
        $.ajax({
            url: $( this ).attr("action"),
            type: 'POST',
            data: data_form,
            processData: false,
            contentType: false
        }).done(function(data){
            //alert('OK');
            $(".loadingformfiles").hide();
            $("#listfiles").show();
            $(this).show();
            show_folder_files(data);
        }).fail(function($xhr){
            $(this).show();
            $(".loadingformfiles").hide();
            $("#listfiles").show();
            var data = $xhr.status+ " : " +$xhr.statusText;
            showalert(gettext("Error during exchange") + "("+data+")<br/>"+gettext("No data could be stored."), "alert-danger");
        });
    });
/****** CHANGE FILE ********/
  $(document).on('hide.bs.modal', '#folderModalCenter', function (event) {
    event.stopPropagation();
  });

  $(document).on('show.bs.modal', '#folderModalCenter', function (event) {
    //event.preventDefault();
    event.stopPropagation();

    let button = $(event.relatedTarget) // Button that triggered the modal
    let modal = $(this);
    modal.find('form').hide();
    let folder_id = button.data('folderid');

    let filetype = button.data('filetype');
    switch (filetype) {
      case 'CustomImageModel':
        $('#folderModalCenterTitle').html(gettext("Change")+ " "+button.data('filename'));
        modal.find('.modal-body input#id_folder').val(folder_id);
        modal.find('.modal-body input#id_image').val(button.data('fileid'));
        modal.find('.modal-body input#file_type').val(button.data('filetype'));
        $("#formchangeimage").show();
        break;
      case 'CustomFileModel':
        $('#folderModalCenterTitle').html(gettext("Change")+ " "+button.data('filename'));
        modal.find('.modal-body input#id_folder').val(folder_id);
        modal.find('.modal-body input#file_id').val(button.data('fileid'));
        modal.find('.modal-body input#file_type').val(button.data('filetype'));
        $("#formchangefile").show();
        break;
      default:
        $("#folderFormName").show();
        $('#folderModalCenterTitle').html(gettext("Enter new name of folder"));
        let oldname = button.data('oldname') // Extract info from data-* attributes
        // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
        // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
        modal.find('.modal-body input#folderInputName').val(oldname).trigger('focus');
        modal.find('.modal-body input#formfolderid').val(folder_id);
        break;
    }

  });

  function reloadRemoveBtn(){
    let remove = gettext('Remove')
    $("#shared-people").html("")
    $.ajax(
      {
          type: "GET",
          url: "/podfile/ajax_calls/folder_shared_with?foldid=" + $('#formuserid').val(),
          cache: false,
          success: function (response) {
              response.forEach(elt => {
                  $("#shared-people").append('<li class="list-group-item">' + elt.first_name+' '+elt.last_name+(((!HIDE_USERNAME)?' ('+elt.username+')': '')  + ' <button type="button" data-userid=' +elt.id + ' class="btn btn-danger btn-share btn-remove">'+remove+'</button></li>'));
              })
          },
          error : function(result, status, error){
            showalert(gettext("Server error") + "<br/>"+error, "alert-danger");
          }
      }
  );
  }

  function reloadAddBtn(searchTerm){
    var foldid = $("#formuserid").val();
    let add = gettext('Add')
    $.ajax(
        {
            type: "GET",
            url: "/podfile/ajax_calls/search_share_user?term=" + searchTerm + "&foldid=" + foldid,
            cache: false,
            success: function (response) {
                $("#user-search").html("");
                response.forEach(elt => {
                  $("#user-search").append('<li class="list-group-item">' +  (elt.first_name+' '+elt.last_name+(((!HIDE_USERNAME)?' ('+elt.username+')': '')))   + '<button type="button" data-userid=' + elt.id  +' class="btn btn-success btn-share btn-add">' +add+ '</button></li>')
                  
                })
            },
            error : function(result, status, error){
              showalert(gettext("Server error") + "<br/>"+error, "alert-danger");
            }
        }
    );
  }

  $(document).on('show.bs.modal', '#shareModalCenter', function (event) {
    $("#shared-people").text("")
    let button = $(event.relatedTarget)
    let folder_id = button.data('folderid');
    let modal = $(this);
    modal.find('#formuserid').val(folder_id);
    reloadRemoveBtn();
  


  });



  $(document).on("click", ".btn-remove", function(e) {
    $.ajax(
      {
          type: "GET",
          url: "/podfile/ajax_calls/remove_shared_user?foldid=" + $('#formuserid').val() + "&userid=" + $(this).data("userid"),
          cache: false,
          success: function (response) {
            reloadRemoveBtn()
          },
          error : function(result, status, error){
            showalert(gettext("Server error") + "<br/>"+error, "alert-danger");
          }
      },
      
  );
  });


  $(document).on("click", ".btn-add", function(e) {
    $.ajax(
      {
          type: "GET",
          url: "/podfile/ajax_calls/add_shared_user?foldid=" + $('#formuserid').val() + "&userid=" + $(this).data("userid"),
          cache: false,
          success: function (response) {
            reloadAddBtn($("#userInputName").val())
            reloadRemoveBtn()
          },
          error : function(result, status, error){
            showalert(gettext("Server error") + "<br/>"+error, "alert-danger");
          }
      }
  );
  });


  $(document).on("click", "#modalSave", function(e) {
    $( "#folderModalCenter form:visible" ).submit();
  });



  $(document).on("click", "#currentfolderdelete", function(e) {
    var deleteConfirm = confirm(gettext("Are you sure you want to delete this folder?"));
    if (deleteConfirm){
        let id = $(this).data('folderid');
        let csrfmiddlewaretoken = $(this).find('input').val();
        send_form_data(deletefolder_url, {'id':id, 'csrfmiddlewaretoken':csrfmiddlewaretoken}, "reloadFolder");
    }
  });

  $(document).on("click", ".btn-delete-file", function(e) {
    var deleteConfirm = confirm(gettext("Are you sure you want to delete this file?"));
    if (deleteConfirm){
        let id = $(this).data('fileid');
        let classname = $(this).data('filetype');
        let csrfmiddlewaretoken = $(this).find('input').val();
        send_form_data(deletefile_url, {'id':id, 'classname':classname, 'csrfmiddlewaretoken':csrfmiddlewaretoken}, "show_folder_files");
    }
  });

  $(document).on('submit', 'form#folderFormName', function(e){
    e.preventDefault();

    send_form_data($(this).attr("action"), $(this).serializeArray(), "reloadFolder");
  });


  $(document).on('input',"#folder-search",function(e) {
    var text = $(this).val().toLowerCase()
    if(text.length > 1 || text.length == 0){
      $("#list_folders_sub").html("")
      let type = $("#list_folders_sub").data("type")
      let currentFolder = getCurrentSessionFolder();
      $.ajax(
        {
            type: "GET",
            url: "/podfile/ajax_calls/user_folders?search=" + text,
            cache: false,
            success: function (response) {
              let nextPage = response.next_page;
                response.folders.forEach(elt => {
                  $("#list_folders_sub").append('<div style="padding:0; margin:0;">' + createFolder(elt.id,elt.name,(currentFolder == elt.name),type,elt.owner) + '</div>')
                })
                if(nextPage != -1){
                  $("#list_folders_sub").append('<a id="more" href="#" data-search="'+text +'" data-next="/podfile/ajax_calls/user_folders?page='+ nextPage +'&search='+ text+'"><div style="padding:0; margin:0;"><img src="' +static_url+ "podfile/images/more.png" + '"/>  Voir plus ('+ (response.current_page+1)+ '/'+ response.total_pages +')</a>' + '</div>')
                }
            }
        }
    );
    }

  });


  $(document).on('input',"#userInputName",function(e) {
    if($(this).val() && $(this).val().length > 2) {
      var searchTerm = $(this).val();
      reloadAddBtn(searchTerm)
    } else {
      $("#user-search").html("");
    }
  });
  
  

  function reloadFolder(data){
    if(data.list_element) {
        var folder_id = data.folder_id;

        if(data.folder_name){
          $("#folder-name-"+ folder_id).text("  "+data.folder_name)
        }
   

        if(data.new_folder == true){
          let type = $("#list_folders_sub").data("type")
          $("#list_folders_sub").prepend('<div style="padding:0; margin:0;">' + createFolder(data.folder_id,data.folder_name,true,type,undefined) + '</div>')
        }

        if(data.deleted){
         $("#folder_" + data.deleted_id).remove()
        }
        send_form_data("/podfile/get_folder_files/"+ folder_id, {}, "show_folder_files", "get");
    
        //dismiss modal
        $('#folderModalCenter').modal('hide');
        $('#folderModalCenter').find('.modal-body input#folderInputName').val("");
        $('#folderModalCenter').find('.modal-body input#formfolderid').val("");

    } else {
        showalert(gettext('You are no longer authenticated. Please log in again.'), "alert-danger");
    }
  }


  function show_folder_files(data){
    if(data.list_element) {
        $('#files').html(data.list_element);
        $(".list_folders a").removeClass('font-weight-bold');
        $("img.directory-image").attr("src", static_url + "podfile/images/folder.png");
        $("img.home-image").attr("src", static_url + "podfile/images/home_folder.png");
        $('#folder_'+data.folder_id).addClass('font-weight-bold');
        $('#folder_'+data.folder_id+" img").attr('src', static_url + "podfile/images/opened_folder.png");


        //dismiss modal
        $('#folderModalCenter').modal('hide');
        $('#folderModalCenter').find('.modal-body input#folderInputName').val("");
        $('#folderModalCenter').find('.modal-body input#formfolderid').val("");

        if(data.upload_errors && data.upload_errors != "") {
            const str = data.upload_errors.split('\n').join('<br/>');
            showalert(gettext("Error during exchange") + "<br/>"+str, "alert-danger");
        }

    } else {
        if(data.errors) {
          showalert(data.errors+"<br/>"+data.form_error, "alert-danger");
        } else {
          showalert(gettext('You are no longer authenticated. Please log in again.'), "alert-danger");
        }
    }
  }

  function append_folder_html_in_modal(data){
    $("#modal-folder_"+id_input).html(data);
  }


  function getCurrentSessionFolder(){
    let folder = "home"
    $.ajax(
      {
          type: "GET",
          url: "/podfile/ajax_calls/current_session_folder/",
          cache: false,
          async: false,
          success: function (response) {
             folder = response.folder
          }
      }
  );
  return folder
  }

  function createFolder(foldid, foldname, isCurrent,type,owner=undefined){
    let construct = ""
    construct+= ('<a href="#" class="folder ' +( isCurrent ? 'font-weight-bold' : '') + ' " id="folder_' + foldid + '" data-foldname="' + foldname + '" data-id="' + foldid+ '" data-target="');
    let isType = (type != "None" && type != undefined)
    construct+= ('/podfile/get_folder_files/' + foldid + (isType ? ('?type=' +type) : "") + '"')
    if(owner != undefined){
      foldname = '<i><span id="folder-name-'+ foldid + '">  ' + foldname + '</span></i> <b>(' + owner+')</b>' 
    }
    else{
      foldname = '<span id="folder-name-' +foldid +  '">  ' +foldname+ '</span>'
    }
    construct+= ('><img class="directory-image" src="' + (isCurrent ? (static_url +'podfile/images/opened_folder.png') : (static_url + 'podfile/images/folder.png') )+'"/>'+foldname+'</a>')
    return construct
  }

  function initFolders(){
    let type = $("#list_folders_sub").data("type")
    let currentFolder = getCurrentSessionFolder();
    $.ajax(
      {
          type: "GET",
          url: "/podfile/ajax_calls/user_folders",
          cache: false,
          success: function (response) {
              let nextPage = response.next_page;
              response.folders.forEach(elt => {
                $("#list_folders_sub").append('<div style="padding:0; margin:0;">' + createFolder(elt.id,elt.name,(currentFolder == elt.name),type,elt.owner) + '</div>')
              })
              if(nextPage != -1){
                $("#list_folders_sub").append('<a id="more" href="#" data-next="/podfile/ajax_calls/user_folders?page='+ nextPage +'"><div style="padding:0; margin:0;"><img src="' +static_url+ "podfile/images/more.png" + '"/>  '+ gettext('See more')+' ('+ (response.current_page+1)+ '/'+ response.total_pages +')</a>' + '</div>')
              }
         
          }
      }
  );
  }
  $(document).ready(function(e) {
    if(typeof myFilesView !== 'undefined'){
      initFolders();
    }
  });



  $(document).on("click","#more", function(e) {
    let next = $(this).data("next")
    let search = $(this).data("search")
    let currentFolder = getCurrentSessionFolder();
    let type = $("#list_folders_sub").data("type")
    $(this).remove()
    $.ajax(
      {
          type: "GET",
          url: next,
          cache: false,
          success: function (response) {
            let nextPage = response.next_page
               response.folders.forEach(elt => {
                $("#list_folders_sub").append('<div style="padding:0; margin:0;">' + createFolder(elt.id,elt.name,(currentFolder == elt.name),type,elt.owner) + '</div>')
              })
              if(nextPage != -1){
                $("#list_folders_sub").append('<a id="more" href="#" data-next="/podfile/ajax_calls/user_folders?page='+nextPage + ((search!=undefined) ? ('&search='+search) : '' ) + '"><div style="padding:0; margin:0;"><img src="' +static_url+ "podfile/images/more.png" + '"/>  Voir plus ('+ (response.current_page+1)+ '/'+ response.total_pages +')</a>' + '</div>')
              }
              
          }
      }
  );
  })


  $(document).on('show.bs.modal', '.podfilemodal', function (event) {
    event.stopPropagation();
    setTimeout(function(){initFolders()}, 500);
    
  });


/*
var send_form_data = function(url,data_form, fct, method="post") {
    var jqxhr= '';
    if(method=="post") jqxhr = $.post(url, data_form);
    else jqxhr = $.get(url);
    jqxhr.done(function(data){ window[fct](data); });
    jqxhr.fail(function($xhr) {
        var data = $xhr.status+ " : " +$xhr.statusText;
        showalert(gettext("Error during exchange") + "("+data+")<br/>"+gettext("No data could be stored."), "alert-danger");
    });
}
*/
}
