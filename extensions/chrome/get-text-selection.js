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
	"title": "Copy to Local Plan extension",
	"contexts": ["page", "selection", "image", "link"],
	"onclick": clickHandler
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
