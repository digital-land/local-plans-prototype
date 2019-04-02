
'use strict';

// ------------------
// DOM util functions
// ------------------

// classes can be str or Array of class names
function createElementWithClasses(tag, classes) {
  const element = document.createElement(tag);
  if(Array.isArray(classes)) {
    element.classList.add(...classes);
  } else {
    element.classList.add(classes);
  }
  return element;
}


function insertAfter(el, referenceNode) {
  referenceNode.parentNode.insertBefore(el, referenceNode.nextSibling);
}


// takes a newly created element -> wrapper
// and an element -> el to be wrapped
function wrapElement(el, wrapper) {
  el.parentNode.insertBefore(wrapper, el);
  wrapper.appendChild(el);
}


function switchClasses(el, toAdd, toRemove) {
  el.classList.remove(toRemove);
  el.classList.add(toAdd);
}

// ------------------
// Helper functions
// ------------------

function cleanNumber(str) {
  // strip any commas user may have added
  return str.replace(/\,/g, "");
}


function postJSONRequest(endpoint, data, cb) {
  fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  })
  .then(response => response.json())
  .then(resp_data => {
    if(cb && typeof cb === "function") {
      cb(resp_data);
    } else {
      console.log(resp_data);
    }
  });
}

// ------ end Helper functions -------
