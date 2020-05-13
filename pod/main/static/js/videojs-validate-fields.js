// Validate input type date (video date_delete)
window.onload = function()
{
    // get selected lang and save it in localStorage
    let lang_btn = document.querySelector(".btn-lang.btn-lang-active");
    let lang = lang_btn?lang_btn.textContent.trim() : "fr";
    if(!localStorage.getItem('lang') || (localStorage.getItem('lang') && lang_btn) )
        localStorage.setItem('lang', lang)
    
    let dtf = new Intl.DateTimeFormat(lang,{day:"2-digit", month:"2-digit", year:"numeric"});
    let input = document.querySelector("input#id_date_delete") || document.querySelector('input[name="date_delete"');
    input.setAttribute("type", "date");
    let given = new Date(input.value)
    let limite = new Date();
    limite.setYear((new Date()).getFullYear() + max_duration_date_delete)
    let listener_inputchange = function()
    {
        given = new Date(input.value);
        let error_message = document.createElement("span");
        if(given > limite)
        {
            let msg = localStorage.getItem('lang') == 'en' ? 'The date must be before or equal to' : 'La date doit être antérieur au'
            // Create message span element with error_message class and
            // Add error_value class to the input field
            input.classList.add("error_value")
            input.style.borderColor = "red";
            //<span class="error_message">The date must be before or equal to</span>
            error_message.classList.add("error_message");
            error_message.style.color= "red";
            error_message.style.display= "inline-block";
            error_message.style.marginLeft= "5px";
            error_message.textContent = `${msg} ${dtf.format(limite)}`;
            //error_message.textContent = `The date must be before or equal to ${limite.toLocaleDateString()}`;
            
            // Insert the message span at the last position in parentElement
            if(!input.parentElement.querySelector('span.error_message'))
                input.parentNode.appendChild(error_message);
        }
        else if(input.parentElement.querySelector('span.error_message'))
        {
            input.parentElement.removeChild(input.parentElement.querySelector('span.error_message'));
            input.classList.remove('error_value')
            input.style.borderColor= "#ccc";
        }
    }
    // Set listener on the field and check even after reloading the page
    input.onchange = function(){ listener_inputchange(); }
    listener_inputchange()
};
