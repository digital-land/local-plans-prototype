// for use with script injection method
// chrome.runtime.sendMessage({
//   action: "getTextSelection",
//   textSelection: window.getSelection().toString()
// });

// chrome.contextMenus.create({id:"lookup",title:"Lookup %s",contexts:["selection"]});
// chrome.contextMenus.onClicked.addListener(function(sel){
//        console.log(sel.selectionText);
// });

var parent = chrome.contextMenus.create({
	"id": "get-selection",
	"title": "Copy to Local Plan extension",
	"contexts": ["page", "selection", "image", "link"]
});

chrome.contextMenus.onClicked.addListener(function(info, tab) {
	if(info.menuItemId == "get-selection") {
		clickHandler(info);
	} else if (info.menuItemId == "screen-cap") {
		capScreenClickHandler(info);
	}
});

function clickHandler(e) {
	console.log(e);

	// if looking at doc
	if(e.pageUrl.startsWith('chrome-extension://')) {
		console.log("Looking at a document e.g. a .pdf");

		const textSelection = e.selectionText;
		// do something
		(e.linkUrl) ? console.log("TEXT + LINK"):console.log("TEXT");

	// must be a webpage
	} else {

		// is it an image
		if(e.mediaType === "image") {
			const imgUrl = e.srcUrl;
			// do something
			console.log("IMAGE");
		// is it a link
		} else if (e.linkUrl) {
			const link = e.linkUrl;
			// do something
			console.log("LINK");
		// just text selected
		} else {
			const text = e.selectionText;
			// do something
			console.log("TEXT");
		}
	}
}

var screenCap = chrome.contextMenus.create({
	"id": "screen-cap",
	"title": "MHCLG screen cap",
	"contexts": ["all"]
});

let id = 111;
function capScreenClickHandler(e) {
	// capture the screenshot
	chrome.tabs.captureVisibleTab(function(screenshotDataUrl) {
		// screenshot.html -> the html page that we push the screenshot to
		const screenshotViewerTabUrl = chrome.extension.getURL('screenshot.html?id=' + id++);
		let targetId = null;
		console.log("DEBUG");

		// listen for tab opening and loading
		chrome.tabs.onUpdated.addListener(function listener(tabId, changedProps) {
			console.log("something something");
			// check tab we are about to open has loaded
			if(tabId != targetId || changedProps.status != "complete") {
				console.log(tabId, " vs ", targetId);
				console.log(changedProps.status);
				return;
			}

			// if it's loaded then don't need to keep lostening out
			chrome.tabs.onUpdated.removeListener(listener);


			// find the tab we just opened and add the screenshot to is
			const views = chrome.extension.getViews();
			for (var i = 0; i < views.length; i++) {
				const view = views[i];
				if(view.location.href == screenshotViewerTabUrl) {
					// this is a function made available my 
					// screenshot.js
					view.setScreenshotUrl(screenshotDataUrl);
					break;
				}
			}
		});

		// the bit that opens the new tab
		chrome.tabs.create({url: screenshotViewerTabUrl}, function(tab) {
      		targetId = tab.id;
    	});
	});
}
