'use strict';

let toggle = document.getElementById('local-plan-database');
let environment = document.getElementById('environment');

function changeState(state) {
  if(state === 'live') {
      toggle.checked = true;
      environment.innerHTML = 'live';
  } else {
      toggle.checked = false;
      environment.innerHTML = 'test local';
  }
}

chrome.storage.onChanged.addListener(function(data) {
  if (data.localPlanUrl.newValue.indexOf('herokuapp') !== -1) {
    changeState('live');
  } else {
    changeState('test');
  }
});

toggle.onchange = function() {
  if(toggle.checked) {
    chrome.storage.sync.set({ localPlanUrl: 'https://local-plans-prototype.herokuapp.com/' });
  } else {
    chrome.storage.sync.set({ localPlanUrl: 'https://localhost:5000/' });
  }
}

chrome.storage.sync.get(['localPlanUrl'], function(data) {
  if(typeof data.localPlanUrl === 'undefined' || data.localPlanUrl.indexOf('herokuapp') !== -1) {
    changeState('live');
  } else {
    changeState('test');
  }
});
