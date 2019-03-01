// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// This extension demonstrates using chrome.downloads.download() to
// download URLs.

var allLinks = [];
var visibleLinks = [];

// Display all visible links.
function showLinks() {
  var checkboxContainer = document.querySelector(".govuk-checkboxes__list");
  while (checkboxContainer.firstChild) checkboxContainer.removeChild(checkboxContainer.firstChild);
  var elToCopy = document.querySelector(".govuk-checkboxes__item");

  var linksList = document.getElementById('links');
  while (linksList.children.length > 1) {
    linksList.removeChild(linksList.children[linksList.children.length - 1])
  }
  for (var i = 0; i < visibleLinks.length; ++i) {
    var item = elToCopy.cloneNode(true);
    var label = item.querySelector("label");
    var input = item.querySelector("input");

    label.textContent = visibleLinks[i];
    label.setAttribute("for", `url-${i}`);
    label.classList.remove("govuk-!-font-weight-bold");

    input.setAttribute('id', `url-${i}`);
    input.value = visibleLinks[i];
    checkboxContainer.appendChild( item );
  }
}

// Toggle the checked state of all visible links.
function toggleAll() {
  var checked = document.getElementById('toggle').checked;
  for (var i = 0; i < visibleLinks.length; ++i) {
    document.getElementById('url-' + i).checked = checked;
  }
}

// Note the url to post to is hard coded. Need to work out how to make user choose an
// option to set destination url but this is for local test at this point
function saveDocuments() {
  toSend = [];
  for (var i = 0; i < visibleLinks.length; ++i) {
    if (document.getElementById('url-' + i).checked) {
      console.log('post this to back end => ' + visibleLinks[i]);
      toSend.push(visibleLinks[i]);
    }
  }
  if (toSend.length > 0) {
    checkLink = document.getElementById('local-authority')

    fetch('http://localhost:5000/local-plans/add-document', {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          'documents': toSend,
          'planning_authority': window.location.origin,
          'active_page_origin': activePageDetails["currentOrigin"] || "",
          'active_page_location': activePageDetails["currentLocation"] || ""})
      })
      .then(response => response.json())
      .then( (resp_data) => checkLink.innerHTML = resp_data['check_page'] );
  }
}

function createStageTag(plan) {
  //<span class="stage-tag plan-details__item is-adopted">adopted</span>
  var tagElement = document.createElement('span');
  tagElement.classList.add('stage-tag');
  tagElement.textContent = plan['id'];
  return tagElement;
}

function displayPageDetails(pla_obj) {
  var pageDetailsContainer = document.querySelector(".page-details");
  var planList = document.querySelector(".plan-list");
  var nameElement = pageDetailsContainer.querySelector(".pla-name");
  console.log(pla_obj.name);
  nameElement.textContent = pla_obj.name;
  pla_obj['plans'].forEach((plan) => {
    planList.appendChild( createStageTag(plan) );
  });
}

function checkPageBelongsToAuthority(pageDetails) {

  fetch('http://localhost:5000/local-plans/check-url', {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        'active_page_origin': activePageDetails["currentOrigin"] || "",
        'active_page_location': activePageDetails["currentLocation"] || ""})
    })
    .then(response => response.json())
    .then( (resp_data) => {
      //console.log(resp_data);
      displayPageDetails(resp_data.planning_authority);
    });

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

var activePageDetails = {};
(function($) {
  $(function () {

    // Set up event handlers and inject send_links.js into all frames in the active
    // tab.

    document.getElementById('toggle').onchange = toggleAll;
    document.getElementById('save').onclick = saveDocuments; 

    chrome.windows.getCurrent(function (currentWindow) {
      chrome.tabs.query(
        { active: true, windowId: currentWindow.id },
        function(activeTabs) {
          chrome.tabs.executeScript(activeTabs[0].id, {file: 'send_links.js', allFrames: true});
        }
      );
    });
  });

  // inject fetch-page-details.js and listen for 
  // page returning details in a message
  chrome.tabs.executeScript(null, {
    file: "fetch-page-details.js"
  });

  chrome.runtime.onMessage.addListener(function (request, _sender) {
    if (request.action == "fetchPageDetails") {
      activePageDetails = {
        "currentLocation": request.currentLocation,
        "currentHost": request.currentHost,
        "currentOrigin": request.currentOrigin,
        "currentPathname": request.currentPathname,
        "windowHeight": request.windowHeight
      }
      checkPageBelongsToAuthority(activePageDetails);
      console.log(activePageDetails);
    }
  });
}(jQuery));
