var tree_fields = document.getElementById('tree-fields');

window.addEventListener('load', function() {
    var tree_num = 1;
    for (const tree of data.trees) {
        if (!document.getElementById('tree' + tree_num + '-species')) {
            add_tree_field();
        }
        document.getElementById('tree' + tree_num + '-species').value = tree.name;
        tree_num++;
    }
})

function add_tree_field() {
    console.log("add tree");
    var tree_num = tree_fields.getElementsByClassName('form-group').length + 1;
    var field_group = document.createElement('div');
    field_group.setAttribute('class', 'form-group');

    var label = document.createElement('label');
    label.innerHTML = 'Tree ' + tree_num + ' species';
    var input = document.createElement('input')
    input.setAttribute('type','text');
    input.setAttribute('name','tree' + tree_num + '_species');
    input.setAttribute('id','tree' + tree_num + '-species');
    input.setAttribute('class','form-control');
    input.setAttribute('required', '');
    input.setAttribute('readonly', '');

    field_group.appendChild(label);
    field_group.appendChild(input);

    tree_fields.appendChild(field_group);
}