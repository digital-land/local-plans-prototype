chrome.runtime.sendMessage({
  action: "fetchPageDetails",
  currentLocation: window.location.href,
  currentHost: window.location.host,
  currentOrigin: window.location.origin,
  currentPathname: window.location.pathname,
  windowHeight: window.innerHeight
});
