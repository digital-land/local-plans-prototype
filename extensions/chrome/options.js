'use strict';

const toggle = document.getElementById('local-plan-database');
const environment = document.getElementById('environment');

function changeState(event) {
  if(event.target.checked) {
    chrome.storage.sync.set({ localPlanUrl: 'https://local-plans-prototype.herokuapp.com/' });
    environment.innerHTML = 'live';
  } else {
    chrome.storage.sync.set({ localPlanUrl: 'https://localhost:5000/' });
    environment.innerHTML = 'test local';
  }
}

toggle.onchange = changeState;

chrome.storage.sync.get(['localPlanUrl'], data => {
  const event = new Event('change');
  if(typeof data.localPlanUrl === 'undefined' || data.localPlanUrl.includes('herokuapp')) {
    toggle.checked = true;
  }
  toggle.dispatchEvent(event);
});
