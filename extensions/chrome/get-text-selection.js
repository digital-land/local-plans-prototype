chrome.runtime.sendMessage({
  action: "getTextSelection",
  textSelection: window.getSelection().toString()
});
