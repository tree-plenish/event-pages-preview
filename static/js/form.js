var host_fields = document.getElementById('host-fields');
var add_host_fields = document.getElementById('add-host-fields');
var remove_host_fields = document.getElementById('remove-host-fields');

var tree_fields = document.getElementById('tree-fields');
var add_tree_fields = document.getElementById('add-tree-fields');
var remove_tree_fields = document.getElementById('remove-tree-fields');

add_host_fields.onclick = function(){
    console.log("add host");
    var host_num = host_fields.getElementsByClassName('host-field').length + 1;
    var field_group = document.createElement('div');
    field_group.setAttribute('class', 'host-field');

    var title = document.createElement('h4');
    title.innerHTML = 'Host ' + host_num;

    field_group.appendChild(title);
    field_group.appendChild(host_field('Name', 'text', 'host' + host_num + '_name', true));
    field_group.appendChild(host_field('Bio', 'text', 'host' + host_num + '_bio', true));
    field_group.appendChild(host_field('Photo', 'file', 'host' + host_num + '_photo', false));

    host_fields.appendChild(field_group);
}

function host_field(label_text, type, name, required) {
    var field = document.createElement('div');
    field.setAttribute('class', 'form-group');
    var label = document.createElement('label');
    label.innerHTML = label_text;
    var input = document.createElement('input');
    if (required) input.setAttribute('required', '');
    input.setAttribute('type',type);
    input.setAttribute('name',name);
    input.setAttribute('class','form-control');
    field.appendChild(label);
    field.appendChild(input);
    return field;
}

add_tree_fields.onclick = function(){
    console.log("add tree");
    var tree_num = tree_fields.getElementsByClassName('form-group').length + 1;
    var field_group = document.createElement('div');
    field_group.setAttribute('class', 'form-group');

    var label = document.createElement('label');
    label.innerHTML = 'Tree ' + tree_num + ' species';
    var input = document.createElement('input')
    input.setAttribute('type','text');
    input.setAttribute('name','tree' + tree_num + '_species');
    input.setAttribute('class','form-control');
    input.setAttribute('required', '');

    field_group.appendChild(label);
    field_group.appendChild(input);

    tree_fields.appendChild(field_group);
}

// var loadFile = function(event) {
// 	console.log(URL.createObjectURL(event.target.files[0]));
//     console.log(event.target.files[0]);
//     var image = document.getElementById('output');
// 	image.src = URL.createObjectURL(event.target.files[0]);
// };

remove_host_fields.onclick = function(){
    console.log("remove host");
    var fields = host_fields.getElementsByClassName('host-field');
    if(fields.length >= 2) {
        host_fields.removeChild(fields[(fields.length) - 1]);
    }
}

remove_tree_fields.onclick = function(){
    console.log("remove tree");
    var fields = tree_fields.getElementsByClassName('form-group');
    if(fields.length >= 2) {
        tree_fields.removeChild(fields[(fields.length) - 1]);
    }
}

function selectMediaType(selected) {
    if (selected.value == "Text") {
        document.getElementById("text-group").style.setProperty("display", "block");
        document.getElementById("video-group").style.setProperty("display", "none");
    } else {
        document.getElementById("video-group").style.setProperty("display", "block");
        document.getElementById("text-group").style.setProperty("display", "none");
    }
}