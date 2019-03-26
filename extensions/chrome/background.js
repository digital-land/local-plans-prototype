function blockPdfDownloads(details) {
  let headers = details.responseHeaders;

  const isPdf = headers.some(header => header.value.toLowerCase() === 'application/pdf');

  if(isPdf) {
    headers = headers.filter(header => header.name.toLowerCase() !== 'content-disposition' && header.value.toLowerCase().indexOf('attachment') !== 0);
  }

  if(details.responseHeaders.length !== headers.length) {
    console.log('[LOCAL PLANS]: Headers changed, from', details.responseHeaders, 'to', headers);
  }

  return { responseHeaders: headers };
}

chrome.webRequest.onHeadersReceived.addListener(blockPdfDownloads, {
  urls: ['<all_urls>'],
  types: ['main_frame', 'sub_frame']
}, ['blocking', 'responseHeaders']);
