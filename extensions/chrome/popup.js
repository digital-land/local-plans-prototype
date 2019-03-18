// Copyright (c) 2012 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// This extension demonstrates using chrome.downloads.download() to
// download URLs.

var allLinks = [];
var visibleLinks = [];

var activePlan = undefined;
var pla = undefined;

var planList;

var localPlanUrl = 'http://localhost:5000';

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
  document.querySelector(".document-count").textContent = visibleLinks.length;
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
    const extMessageContainer = document.querySelector('.ext-message');
    const ldsTag = document.querySelector('.stage-tag--lds');

    let dataToSend = {
      'documents': toSend,
      'active_page_origin': activePageDetails["currentOrigin"] || "",
      'active_page_location': activePageDetails["currentLocation"] || ""
    };

    // firstly check if local development scheme is selected
    if(ldsTag.classList.contains('selected')) {
      dataToSend['active_plan'] = "localDevelopmentScheme";
      dataToSend['pla_id'] = "localDevelopmentScheme";
    }
    else if(activePlan !== undefined) {
      dataToSend['active_plan'] = activePlan;
      dataToSend['pla_id'] = pla['id'];
    }

    console.log(dataToSend);

    fetch( localPlanUrl + '/local-plans/add-document', {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(dataToSend)
      })
      .then(response => response.json())
      .then( (resp_data) => {
        if(resp_data['OK'] === 200) {
          extMessageContainer.classList.add("success");
          var linkEl = extMessageContainer.querySelector(".ext-message__link");
          var message = extMessageContainer.querySelector(".ext-message__content");
          linkEl.href = resp_data['check_page'];
          message.innerHTML = "Docs saved successfully. ";
        }
      });
  }
}

function createStageTag(plan, _class) {
  let classes = _class || undefined;
  //<span class="stage-tag plan-details__item is-adopted">adopted</span>
  var tagElement = document.createElement('span');
  (classes === undefined) ? tagElement.classList.add('stage-tag'):tagElement.classList.add('stage-tag', classes);
  tagElement.dataset.planId = plan['id'];
  tagElement.textContent = plan['id'];
  if(plan['is_adopted']) tagElement.classList.add('stage-tag--adopted');
  return tagElement;
}

function setActivePlan(selectedTag) {
  activePlan = selectedTag.dataset.planId;
  const tags = planList.querySelectorAll(".stage-tag");
  tags.forEach((tag) => tag.classList.remove("selected"));
  selectedTag.classList.add("selected");
}

function displayPageDetails(pla_obj) {
  pla = pla_obj;
  var pageDetailsContainer = document.querySelector(".page-details");
  var nameElement = pageDetailsContainer.querySelector(".pla-name");
  console.log(pla_obj.name);
  nameElement.textContent = pla_obj.name;

  const ldsTag = document.querySelector('.stage-tag--lds').classList.remove('selected');

  if(pla_obj['plans'].length === 1) {
    console.log("just the one");
    planList.appendChild( createStageTag(pla_obj['plans'][0], "selected") );
  } else {
    pla_obj['plans'].forEach((plan) => {
      planList.appendChild( createStageTag(plan) );
      console.log(plan);
    });
    planList.querySelector(`[data-plan-id=${pla_obj['plans'][0]['id']}]`).classList.add("selected");
  }
  activePlan = pla_obj['plans'][0]['id'];
}

function populatePlanView(data) {
  const section = document.querySelector('.local-plan-facts-section');
  pla = data.local_plan.planning_authorities[0];

  displayURLAsHeading(data.document.url, section, data.document['id']);

  const form = section.querySelector(".add-fact-form");
  form.action = data.add_fact_url;

  const planEl = section.querySelector('.facts__local-plan');
  planEl.appendChild( createStageTag(data.local_plan, "selected") );
  activePlan = data.local_plan['id'];

  const table = section.querySelector(".document-facts__table");
  const table_body = table.querySelector('tbody');
  if(data.document.facts.length > 0) {
    data.document.facts.forEach((fact) => table_body.appendChild( createFactRow(fact) ));
  } else {
    table.classList.add('govuk-visually-hidden');
  }
}

function displayURLAsHeading(url, section, docId) {
  const urlEl = section.querySelector('.facts__doc-url');
  urlEl.textContent = url;
  urlEl.dataset.documentId = docId;
}

function populateEmergingPlanView(data) {
  const section = document.querySelector('.emerging-plan-facts-section');
  displayURLAsHeading(data.document.url, section, data.document['id']);

  const form = section.querySelector(".add-fact-form");
  form.action = data.add_fact_url;

  const table = section.querySelector(".document-facts__table");
  const table_body = table.querySelector('tbody');
  if(data.document.facts.length > 0) {
    data.document.facts.forEach((fact) => table_body.appendChild( createFactRow(fact) ));
  } else {
    table.classList.add('govuk-visually-hidden');
  }
}

function checkPageBelongsToAuthority(pageDetails) {

  fetch( localPlanUrl + '/local-plans/planning-authority', {
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
      document.body.classList.remove("not-recognised-view");
      //console.log(resp_data);
      if(resp_data['view-type'] === 'plan-document') {
        console.log(resp_data);
        populatePlanView(resp_data);
        document.body.classList.add("local-plan-view");
      } else if (resp_data['view-type'] === 'emerging-plan-document') {
        console.log(resp_data);
        populateEmergingPlanView(resp_data);
        document.body.classList.add("emerging-plan-view");
      } else if (resp_data['view-type'] === 'urls') {
        displayPageDetails(resp_data.planning_authority);
        document.body.classList.add("url-view");
      } else {
        document.body.classList.add("not-recognised-view");
      }
    });

}

function createFactRow(fact) {
  const row = document.createElement('tr');
  row.classList.add('govuk-table__row');

  const row_fact = document.createElement('th');
  row_fact.classList.add('govuk-table__header');
  row_fact.setAttribute('scope', 'row');
  row_fact.textContent = fact.fact;

  const row_type = document.createElement('td');
  row_type.classList.add('govuk-table__cell');
  row_type.textContent = fact.fact_type_display;

  const row_note = document.createElement('td');
  row_note.classList.add('govuk-table__cell');
  row_note.textContent = fact.notes;

  row.appendChild( row_fact );
  row.appendChild( row_type );
  row.appendChild( row_note );

  return row;
}

function extractDate(fieldset) {
  const month = fieldset.querySelector(".govuk-date-input__month");
  const year = fieldset.querySelector(".govuk-date-input__year");
  return `${year.value}-${month.value}`;
}

function extractRange(fieldset) {
  var min = fieldset.querySelector(".housing-req-range-min");
  var max = fieldset.querySelector(".housing-req-range-max");
  return `${min.value} - ${max.value}`;
}

function factSubmitHandler(e) {
  e.preventDefault();
  const form = e.target;
  const url = form.action;

  // set up data obj to post
  // serialise all parts of form
  var fact = {};
  fact["fact_type"] = form.querySelector("select").value;
  fact["notes"] = form.querySelector("textarea").value;
  fact["document_type"] = form.querySelector("input[type='hidden']").value;

  if(form.classList.contains('plan-name')) {
    fact["fact"] = form.querySelector(".plan-name-input input").value;
  } else if (form.classList.contains('plan-start-year')) {
    fact["fact"] = extractDate( form.querySelector(".plan-start-date-input fieldset") );
  } else if (form.classList.contains('plan-end-year')) {
    fact["fact"] = extractDate( form.querySelector(".plan-end-date-input fieldset") );
  } else if (form.classList.contains('housing-requirement-total')) {
    fact["fact"] = form.querySelector(".plan-housing-req-total input").value;
  } else if (form.classList.contains('housing-requirement-range')) {
    fact["fact"] = extractRange( form.querySelector(".housing-req-range-fieldset") );
  } else if (form.classList.contains('publication-date')) {
    fact["fact"] = extractDate( form.querySelector(".publication-date-input fieldset") );
  } else if (form.classList.contains('proposed-reg-18-date')) {
    fact["fact"] = extractDate( form.querySelector(".regulation-18-date-input fieldset") );
  } else if (form.classList.contains('proposed-publication-date')) {
    fact["fact"] = extractDate( form.querySelector(".proposed-publication-date-input fieldset") );
  } else if (form.classList.contains('proposed-submission-date')) {
    fact["fact"] = extractDate( form.querySelector(".proposed-submission-date-input fieldset") );
  } else if (form.classList.contains('proposed-main-modifications-date')) {
    fact["fact"] = extractDate( form.querySelector(".proposed-main-modifications-date-input fieldset") );
  } else if (form.classList.contains('proposed-adoption-date')) {
    fact["fact"] = extractDate( form.querySelector(".proposed-adoption-date-input fieldset") );
  } else {
    // situation where user has selected other
    fact["fact"] = "";
  }

  // if screenshot has been taken add to fact obj
  const screenshotDataUrl = form.querySelector(".screenshot-taker__viewer").src;
  if(screenshotDataUrl !== "") {
    fact["screenshot"] = screenshotDataUrl;
  }

  console.log(fact, url);

  // perform post
  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ 'fact': fact })
  })
  .then(response => response.json())
  .then( (resp_data) => {
    if(resp_data['OK'] === 200) {
      console.log(resp_data);
      const factsEl = form.closest(".document-facts");
      const table = factsEl.querySelector(".document-facts__table");
      displayFact(resp_data, table);
      table.classList.remove('govuk-visually-hidden');
      resetFactForm(form);
    }

  });
}

function displayFact(data, table) {
  const row = createFactRow(data.fact);
  const table_body = table.querySelector('tbody');
  table_body.appendChild( row );
}

function openNewTab(linkEl) {
  const url = linkEl.href;
  if(url !== "") {
    chrome.tabs.create({
      url: url,
      active: false
    });
  } else {
    console.log("href not set");
  }
}

function resetFactForm(form) {
  form.reset();
  const formType = form.querySelector("input[type='hidden']").value;

  // remove all classes
  removeAllClassesFromFactForm(form);
  // add initial class relevant to type of fact
  if(formType === "plan_document") {
    form.classList.add('plan-name');
  } else {
    form.classList.add('publication-date');
  }
  // reset screenshot taker
  resetScreenshotTaker(form.querySelector(".screenshot-taker__details"));
}

function setUpAddFactForms() {
  // handle changes to form when user changes select
  const addFactForms = document.querySelectorAll(".add-fact-form");
  const addFactSelects = Array.prototype.slice.call( addFactForms ).map((form) => form.querySelector(".fact-select-types"));
  addFactSelects.forEach((select) => {
    select.addEventListener('change', (e) => {
      const form = e.target.closest('form');
      const option = e.target.querySelector('option:checked');
      // remove all these classes before adding selected class
      removeAllClassesFromFactForm(form);
      form.classList.add(option.dataset.typeClass);
    });
  });

  addFactForms.forEach((form) => form.addEventListener('submit', factSubmitHandler));
}

function removeAllClassesFromFactForm(form) {
  form.classList.remove("plan-name", "plan-start-year", "plan-end-year", "housing-requirement-total", "housing-requirement-range", "publication-date", "proposed-reg-18-date", "proposed-publication-date", "proposed-submission-date", "proposed-main-modifications-date", "proposed-adoption-date");
}


function resetScreenshotTaker(detailsEl) {
  // remove dataURL as src
  detailsEl.querySelector(".screenshot-taker__viewer").src = "";
  // reset text changes
  const textEls = detailsEl.querySelectorAll("[data-original-text]");
  textEls.forEach((el) => {
    el.textContent = el.dataset.originalText;
  });
}

function screenshotTaker(screenshotEl) {
  const summary = screenshotEl.closest('details').querySelector(".screenshot-taker__summary span");
  const viewer = screenshotEl.querySelector(".screenshot-taker__viewer");
  const btn = screenshotEl.querySelector(".screenshot-taker__btn");
  let shotTaken = false;

  function clickHandler(e) {
    e.preventDefault();
    chrome.tabs.captureVisibleTab(function(screenshotDataUrl) {
      viewer.src = screenshotDataUrl;
    });

    if(!shotTaken) {
      summary.textContent = "Check screenshot";
      btn.textContent = "Retake";
      shotTaken = true;
    }
  }

  btn.addEventListener('click', clickHandler);
}

// Add links to allLinks and visibleLinks, sort and show them.  send_links.js is
// injected into all frames of the active tab, so this listener may be called
// multiple times.
chrome.runtime.onMessage.addListener(function(request, _sender) {
  if (request.action == "findLinks") {
    const links = request.links;
    for (var index in links) {

      console.log(links[index]);
      allLinks.push(links[index]);

    }
    allLinks.sort();
    visibleLinks = allLinks;
    showLinks();
  }
});

var activePageDetails = {};
(function($) {
  $(function () {

    planList = document.querySelector(".plan-list");

    // Set up event handlers and inject send_links.js into all frames in the active
    // tab.

    document.getElementById('toggle').onchange = toggleAll;
    document.getElementById('save').onclick = saveDocuments;

    planList.addEventListener('click', (e) => {
      const target = e.target;
      if(target.classList.contains('stage-tag')) {
        setActivePlan(target);
      }
    });

    setUpAddFactForms();

    const docsSavedLink = document.querySelector(".ext-message__link");
    docsSavedLink.addEventListener('click', (e) => openNewTab(e.currentTarget));


    chrome.windows.getCurrent(function (currentWindow) {
      chrome.tabs.query(
        { active: true, windowId: currentWindow.id },
        function(activeTabs) {
          chrome.tabs.executeScript(activeTabs[0].id, {file: 'find_links.js', allFrames: true});
        }
      );
    });

    // set up screenshot taking
    const screenshotTakers = document.querySelectorAll(".screenshot-taker");
    screenshotTakers.forEach(screenshotTaker);

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

  chrome.storage.sync.get(['localPlanUrl'], function(data) {
    if (data.localPlanUrl !== undefined) {
      localPlanUrl = data.localPlanUrl.replace(/\/$/, '');
    }
  });

}(jQuery));
