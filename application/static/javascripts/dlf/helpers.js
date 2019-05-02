/* eslint no-unused-vars: 0 */

// ------------------
// DOM util functions
// ------------------

// classes can be str or Array of class names
function createElementWithClasses(tag, classes) {
  const element = document.createElement(tag);
  if (Array.isArray(classes)) {
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
  return str.replace(/,/g, "");
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
    .then(respData => {
      if (cb && typeof cb === "function") {
        cb(respData);
      } else {
        console.log(respData); // eslint-disable-line
      }
    });
}

function postFormDataRequest(endpoint, data, cb) {
  // useful for seeing what FormData is
  // for (var pair of data.entries()) {
  //     console.log(pair[0]+ ', '+ pair[1]); 
  // }

  fetch(endpoint, {
    method: "POST",
    body: data
  })
    .then(response => response.json())
    .then(respData => {
      if (cb && typeof cb === "function") {
        cb(respData);
      } else {
        console.log(respData); // eslint-disable-line
      }
    });
}

// @function setOptions(obj: Object, options: Object): Object
// Merges the given properties to the `options` of the `obj` object, returning the resulting options.
// Based on setOptions in LeafletJS Class
function setOptions(obj, options) {
  if (!obj.hasOwnProperty("options")) {
    obj.options = obj.options || {};
  }
  for (var i in options) {
    obj.options[i] = options[i];
  }
  return obj.options;
}

// ------ end Helper functions -------
