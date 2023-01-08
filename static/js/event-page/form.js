var host_fields = document.getElementById('host-fields');
var add_host_fields = document.getElementById('add-host-fields');
var remove_host_fields = document.getElementById('remove-host-fields');

var tree_fields = document.getElementById('tree-fields');


//  modal
var modal = document.getElementById("crop-popup");
var errorModal = document.getElementById("error-popup");
var modalImage = document.getElementById("crop-image");
var imageTester = document.getElementById("image-tester");
var modalImageError = document.getElementById("modal-image-error");

document.getElementById("host1-crop-button").onclick = function() { openModal(1); };

var confirmImage = document.getElementById("confirm-image");
var spanError = document.getElementsByClassName("close")[0];

var activeImgIdx;


window.addEventListener('load', function() {
    if (data.media_type_video) {
        document.getElementById('video').setAttribute("checked", "");
        selectMediaType(document.getElementById('video'));
        document.getElementById('video-box').setAttribute("required", "");
    } else {
        document.getElementById('text').setAttribute("checked", "");
        selectMediaType(document.getElementById('text'));
        document.getElementById('text-box').setAttribute("required", "");
    }
    var host_num = 1;
    for (const host of data.hosts) {
        if (host.display) {
            if (!document.getElementById('host' + host_num + '-name')) {
                add_host_field();
            }
            document.getElementById('host' + host_num + '-name').value = host.name;
            document.getElementById('host' + host_num + '-uuid').value = host.uuid;
            document.getElementById('host' + host_num + '-bio').value = host.bio;
            document.getElementById('host' + host_num + '-photo').value = host.form_photo;
            document.getElementById('host' + host_num + '-photo-x').value = host.photo_x;
            document.getElementById('host' + host_num + '-photo-y').value = host.photo_y;
            document.getElementById('host' + host_num + '-photo-zoom').value = host.photo_zoom;
            host_num++;
        }
    }
    var tree_num = 1;
    for (const tree of data.trees) {
        if (!document.getElementById('tree' + tree_num + '-species')) {
            add_tree_field();
        }
        document.getElementById('tree' + tree_num + '-species').value = tree.name;
        tree_num++;
    }
})

add_host_fields.onclick = function(){
    add_host_field();
}

function add_host_field() {
    console.log("add host");
    var host_num = host_fields.getElementsByClassName('host-field').length + 1;
    var field_group = document.createElement('div');
    field_group.setAttribute('class', 'host-field');

    var title = document.createElement('h4');
    title.innerHTML = 'Team Member ' + host_num;

    var uuid = document.createElement('input');
    uuid.setAttribute('id', "host" + host_num + "-uuid");
    uuid.setAttribute('name', "host" + host_num + "_uuid");
    uuid.setAttribute('type', "hidden");

    field_group.appendChild(title);
    field_group.appendChild(uuid);
    field_group.appendChild(host_field('Name', 'text', 'host' + host_num + '_name', true, null, false));
    field_group.appendChild(host_field('Bio', 'text', 'host' + host_num + '_bio', true, null, false));
    field_group.appendChild(host_field('Photo (Instructions <a target="_blank" href="../static/pdf/photo_instructions.pdf">here</a>)', 'text', 'host' + host_num + '_photo', false, null, false));
    field_group.lastChild.lastChild.setAttribute('onchange', 'openModalCheck(this);');

    var img_options_group = document.createElement('div');
    img_options_group.setAttribute('class', 'inline-input-group');
    img_options_group.appendChild(host_field('x-offset', 'text', 'host' + host_num + '_photo_x', false, '0', true));
    img_options_group.appendChild(host_field('y-offset', 'text', 'host' + host_num + '_photo_y', false, '0', true));
    img_options_group.appendChild(host_field('zoom', 'text', 'host' + host_num + '_photo_zoom', false, '100', true));
    var btn = document.createElement('button');
    btn.setAttribute('id', "host" + host_num +  "-crop-button");
    btn.setAttribute('class', "crop-button");
    btn.setAttribute('type', "button");
    btn.innerHTML = 'Adjust photo position and zoom';
    btn.onclick = function() { openModal(host_num); };
    img_options_group.appendChild(btn);    

    field_group.appendChild(img_options_group);

    host_fields.appendChild(field_group);
}

function host_field(label_text, type, name, required, default_val, hidden) {
    var field = document.createElement('div');
    field.setAttribute('class', 'form-group');
    var label = document.createElement('label');
    label.innerHTML = label_text;
    var input = document.createElement('input');
    if (required) input.setAttribute('required', '');
    if (default_val != null) input.setAttribute('value', default_val);
    input.setAttribute('type',type);
    input.setAttribute('id',name.replaceAll('_', '-'));
    input.setAttribute('name',name);
    input.setAttribute('class','form-control');
    if (hidden) field.setAttribute('style', 'display:none');
    field.appendChild(label);
    field.appendChild(input);
    return field;
}

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

function selectMediaType(selected) {
    if (selected.value == "Text") {
        document.getElementById("text-group").style.setProperty("display", "block");
        document.getElementById("video-group").style.setProperty("display", "none");
        document.getElementById('text-box').setAttribute("required", "");
        document.getElementById('video-box').removeAttribute("required");
    } else {
        document.getElementById("video-group").style.setProperty("display", "block");
        document.getElementById("text-group").style.setProperty("display", "none");
        document.getElementById('video-box').setAttribute("required", "");
        document.getElementById('text-box').removeAttribute("required");
    }
}

function openModal(i) {
    console.log("click");
    imgId = document.getElementById("host" + i + "-photo").value;
    activeImgIdx = i;
    if (imgId != '') {
        imageTester.src = "https://drive.google.com/uc?export=view&id=" + imgId;
        modal.style.display = "block";

        modalImage.style['background-image'] = "url(https://drive.google.com/uc?export=view&id=" + imgId + ")";
        modalImage.style['background-position-x'] = document.getElementById("host" + i + "-photo-x").value + 'px';
        modalImage.style['background-position-y'] = document.getElementById("host" + i + "-photo-y").value + 'px';
        modalImage.style['background-size'] = document.getElementById("host" + i + "-photo-zoom").value + '%';
        slider.value = document.getElementById("host" + i + "-photo-zoom").value;
    } else {
        errorModal.style.display = "block";
    }
}

confirmImage.onclick = function() {
    modal.style.display = "none";
    modalImageError.style.display = 'none';
    document.getElementById("host" + activeImgIdx + "-photo-x").value = modalImage.style['background-position-x'].replace('px', '');
    document.getElementById("host" + activeImgIdx + "-photo-y").value = modalImage.style['background-position-y'].replace('px', '');
    document.getElementById("host" + activeImgIdx + "-photo-zoom").value = modalImage.style['background-size'].replace('%', '').split(" ")[0];
}

spanError.onclick = function() {
    errorModal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
    if (event.target == modal) {
        modalImageError.style.display = 'none';
        modal.style.display = "none";
    } else if (event.target == errorModal) {
        errorModal.style.display = "none";
    }
}

var slider = document.getElementById('zoom-slider');
slider.onclick = function() {
    modalImage.style['background-size'] = slider.value + '%';
}

dragElementBackground(modalImage);

function dragElementBackground(element) {
    
    var startX = 0, startY = 0, endX = 0, endY = 0;
    element.onmousedown = dragStart;
    element.ontouchstart = dragStart;

    function dragStart(e) {
        e = e || window.event;
        e.preventDefault();
        // mouse cursor position at start  
        if (e.clientX) {  // mousemove
            startX = e.clientX;
            startY = e.clientY;
        } else { // touchmove - assuming a single touchpoint
            startX = e.touches[0].clientX
            startY = e.touches[0].clientY
        }
        document.onmouseup = dragStop;
        document.ontouchend = dragStop;
        document.onmousemove = elementDrag;  // call whenever the cursor moves
        document.ontouchmove = elementDrag;
    }

    function elementDrag(e) {
        if (element.style['background-position'] == '') {
            element.style['background-position-x'] = '0px';
            element.style['background-position-y'] = '0px';
        }
        e = e || window.event;
        e.preventDefault();
        // calculate new cursor position
        if (e.clientX) {
            endX = startX - e.clientX;
            endY = startY - e.clientY;
            startX = e.clientX;
            startY = e.clientY;
        } else {
            endX = startX - e.touches[0].clientX;
            endY = startY - e.touches[0].clientY;
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }
        // set the new position
        // console.log(element.style['background-position-x'], endX, parseInt(element.style['background-position-y'].replace('px', '')), endY);
        element.style['background-position-x'] = (parseInt(element.style['background-position-x'].replace('px', '')) - endX) + "px";
        element.style['background-position-y'] = (parseInt(element.style['background-position-y'].replace('px', '')) - endY) + "px";
    }

    function dragStop() {
        // stop moving on touch end / mouse btn is released 
        document.onmouseup = null;
        document.onmousemove = null;
        document.ontouchend = null;
        document.ontouchmove = null;
    }
}

function imageError() {
    console.log("image error");
    modalImageError.style['display'] = 'block';
}

function openModalCheck(field) { 
    if (field.value != "") openModal(field.id.replace(/\D/g,'')); 
}