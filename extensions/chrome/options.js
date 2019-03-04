'use strict';

let currentUrl = document.getElementById('local-plan-url');
let button = document.getElementById('set');

button.addEventListener('click', function() {
    let setUrlTo = document.getElementById('local-plan-url-to-set');
    chrome.storage.sync.set({localPlanUrl: setUrlTo.value}, function() {
        console.log('set url to', setUrlTo.value);
        currentUrl.innerHTML = setUrlTo.value;
    });
});

chrome.storage.sync.get(['localPlanUrl'], function(data) {
    console.log('Currently set url is', data);
    currentUrl.innerHTML = data.localPlanUrl;
});

