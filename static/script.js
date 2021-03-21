let state = {
  img_name: null,
  tag_group: null,
  all_tags: null,
  chosen_tags: null
}

function update_tag_group_display() {
  for (let tag_group of document.getElementById('tags').children) {
    tag_group.className = 'd-none';
  }
  document.getElementById('tag_group' + state.tag_group).className = 'd-block';
}

function update_state(json_resp) {
  state.img_name = json_resp['img_name'];
  state.tag_group = json_resp['tag_group'];
  state.all_tags = json_resp['all_tags'];
  state.chosen_tags = Object.fromEntries(json_resp['all_tags'].map(val => [val, false]));
  update_tag_group_display();
  update_image_source();
  update_chosen_tags(json_resp['chosen_tags']);
}

function save() {
  return fetch('tag_image/' + state.img_name, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      img_name: state.img_name,
      tag_group: state.tag_group,
      chosen_tags: Object.keys(Object.fromEntries(Object.entries(state.chosen_tags).filter(([key, val]) => val)))
    }),
  });
}

function next() {
  return fetch('tag_image/next?' + new URLSearchParams({
    img_name: state.img_name,
    tag_group: state.tag_group
  }), {
    method: 'GET'
  }).then((resp) => {
    resp.json().then((json_resp) => {
      update_state(json_resp);
    });
  });
}

function previous() {
  return fetch('tag_image/previous?' + new URLSearchParams({
    img_name: state.img_name,
    tag_group: state.tag_group
  }), {
    method: 'GET'
  }).then((resp) => {
    resp.json().then((json_resp) => {
      update_state(json_resp);
    });
  });
}

document.addEventListener('keyup', (event) => {
  const keyName = event.key;

  switch (keyName) {
    case 'ArrowLeft':
      previous();
      break;
    case 'ArrowRight':
      next();
      break;
    default:
      return;
  }
}, false);

function init_state() {
  return fetch('metadata', {
    method: 'GET',
  }).then((resp) => {
    resp.json().then((json_resp) => {
      update_state(json_resp);
      subscribe_event_listeners();
    });
  });
}

function update_image_source() {
  let img = document.getElementById('img');
  img.src = 'image/' + state.img_name;
}

function add_or_delete_tag(btn_id) {
  let btn = document.getElementById(btn_id);
  if (btn.classList.contains('btn-outline-primary')) {
    btn.className = "btn btn-primary mt-1 mb-1";
    state.chosen_tags[btn_id] = true;
  } else {
    btn.className = "btn btn-outline-primary mt-1 mb-1";
    state.chosen_tags[btn_id] = false;
  }
  save();
}

function update_chosen_tags(chosen_tags) {
  Object.keys(state.chosen_tags).map(key => {
    state.chosen_tags[key] = false;
    let btn = document.getElementById(key);
    btn.className = "btn btn-outline-primary mt-1 mb-1";
  });
  for (let tag of chosen_tags) {
    state.chosen_tags[tag] = true;
    let btn = document.getElementById(tag);
    btn.className = "btn btn-primary mt-1 mb-1";
  }
}

function subscribe_event_listeners() {
  let tag_groups = document.getElementById('tags').children;
  for (let tag_block of tag_groups) {
    for (let tag_btn of tag_block.children) {
      if (tag_btn.tagName === 'LABEL') {
        tag_btn.onclick = () => {
          add_or_delete_tag(tag_btn.id);
        };
      }
    }
  }

  let export_btn = document.getElementById('export_to_csv');
  export_btn.onclick = () => {
    return fetch('export_to_csv', {
      method: 'GET',
    }).then((resp) => {
      if (resp.status === 201) {
        alert('Csv file was created successfully.')
      }
    });
  }
}

init_state();
