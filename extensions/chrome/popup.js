// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// This extension demonstrates using chrome.downloads.download() to
// download URLs.

var allLinks = [];
var visibleLinks = [];

// Display all visible links.
function showLinks() {
  var linksList = document.getElementById('links');
  while (linksList.children.length > 1) {
    linksList.removeChild(linksList.children[linksList.children.length - 1])
  }
  for (var i = 0; i < visibleLinks.length; ++i) {
    var row = document.createElement('tr');
    var col0 = document.createElement('td');
    var col1 = document.createElement('td');
    var checkbox = document.createElement('input');
    checkbox.checked = true;
    checkbox.type = 'checkbox';
    checkbox.id = 'check' + i;
    col0.appendChild(checkbox);
    col1.innerText = visibleLinks[i];
    col1.style.whiteSpace = 'nowrap';
    col1.onclick = function() {
      checkbox.checked = !checkbox.checked;
    }
    row.appendChild(col0);
    row.appendChild(col1);
    linksList.appendChild(row);
  }
}

// Toggle the checked state of all visible links.
function toggleAll() {
  var checked = document.getElementById('toggle').checked;
  for (var i = 0; i < visibleLinks.length; ++i) {
    document.getElementById('check' + i).checked = checked;
  }
}

// Save all visible checked links.
function saveDocuments() {

  for (var i = 0; i < visibleLinks.length; ++i) {
    if (document.getElementById('check' + i).checked) {
      console.log('****** post this to back end => ' + visibleLinks[i]);
    }
  }
  window.close();
}


// Add links to allLinks and visibleLinks, sort and show them.  send_links.js is
// injected into all frames of the active tab, so this listener may be called
// multiple times.
chrome.extension.onRequest.addListener(function(links) {
  for (var index in links) {

    console.log(links[index]);
    allLinks.push(links[index]);

  }
  allLinks.sort();
  visibleLinks = allLinks;
  showLinks();
});

// Set up event handlers and inject send_links.js into all frames in the active
// tab.
window.onload = function() {

  document.getElementById('toggle').onchange = toggleAll;
  document.getElementById('save').onclick = saveDocuments;

  chrome.windows.getCurrent(function (currentWindow) {
    chrome.tabs.query({active: true, windowId: currentWindow.id},
                      function(activeTabs) {
      chrome.tabs.executeScript(
        activeTabs[0].id, {file: 'send_links.js', allFrames: true});
    });
  });
};
