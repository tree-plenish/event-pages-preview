var host_fields = document.getElementById('host-fields');
var add_host_fields = document.getElementById('add-host-fields');
var remove_host_fields = document.getElementById('remove-host-fields');

// document.addEventListener("DOMContentLoaded", function(event) {
//     host_fields = document.getElementById('host-fields');
//     add_host_fields = document.getElementById('add-host-fields');
//     remove_host_fields = document.getElementById('remove-host-fields');
// });

add_host_fields.onclick = function(){
    console.log("add host");
    var host_num = host_fields.getElementsByClassName('host-field').length + 1;
    var field_group = document.createElement('div');
    field_group.setAttribute('class', 'host-field');

    var title = document.createElement('h4');
    title.innerHTML = 'Host ' + host_num;

    field_group.appendChild(title);
    field_group.appendChild(host_field('Name', 'host' + host_num + '_name'));
    field_group.appendChild(host_field('Bio', 'host' + host_num + '_bio'));
    field_group.appendChild(host_field('Photo', 'host' + host_num + '_photo'));

    host_fields.appendChild(field_group);
}

function host_field(label_text, name) {
    var field = document.createElement('div');
    field.setAttribute('class', 'form-group');
    var label = document.createElement('label');
    label.innerHTML = label_text;
    var input = document.createElement('input')
    input.setAttribute('type','text');
    input.setAttribute('name',name);
    input.setAttribute('class','form-control');
    field.appendChild(label);
    field.appendChild(input);
    return field;
}

remove_host_fields.onclick = function(){
    console.log("remove host");
    var fields = host_fields.getElementsByClassName('host-field');
    if(fields.length >= 2) {
        host_fields.removeChild(fields[(fields.length) - 1]);
    }
}