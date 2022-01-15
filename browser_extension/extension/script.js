/*
content script running on youtube.com
*/

console.log("running script.js");

let browserType = getBrowser();

setTimeout(function(){
    console.log("running setimeout")
    linkFinder();
    return false;
}, 2000);


// boilerplate to dedect browser type api
function getBrowser() {
    if (typeof chrome !== "undefined") {
        if (typeof browser !== "undefined") {
            console.log("detected firefox");
            return browser;
        } else {
            console.log("detected chrome");
            return chrome;
        }
    } else {
        console.log("failed to dedect browser");
        throw "browser detection error"
    };
}


// event handler for download task
function addToDownload(videoId) {

    console.log(`downloading ${videoId}`);
    let payload = {
        "download": {
            "videoId": videoId
        }
    };

    browserType.runtime.sendMessage(payload);

}


// find relevant links to add a button to
function linkFinder() {

    console.log("running link finder");

    var allLinks = document.links;
    for (let i = 0; i < allLinks.length; i++) {
        
        const linkItem = allLinks[i];
        const linkDest = linkItem.getAttribute("href");

        if (linkDest.startsWith("/watch?v=") && linkItem.id == "video-title") {
            var dlButton = document.createElement("button");
            dlButton.innerText = "download";
            var videoId = linkDest.split("=")[1];
            dlButton.setAttribute("data-id", videoId);
            dlButton.setAttribute("id", "ta-dl-" + videoId);
            dlButton.onclick = function(event) {
                var videoId = this.getAttribute("data-id");
                addToDownload(videoId);
            };
            linkItem.parentElement.appendChild(dlButton);
        }
    }
}
