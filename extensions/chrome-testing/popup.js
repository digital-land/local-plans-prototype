
(function($) {
  $(function () {

    const screenshotBtn = document.querySelector(".screenshot-btn");
    screenshotBtn.addEventListener('click', (e) => {
      e.preventDefault();
      chrome.tabs.captureVisibleTab(function(screenshotDataUrl) {
        document.getElementById('screenshot-target').src = screenshotDataUrl;
      });
    });

  });

  // text selection via script injection
  // chrome.tabs.executeScript(null, {
  //   file: "get-text-selection.js"
  // });

  // chrome.runtime.onMessage.addListener(function (request, _sender) {
  //   if (request.action == "getTextSelection") {
  //     console.log("Request: ", request);
  //   }
  // });

}(jQuery));
