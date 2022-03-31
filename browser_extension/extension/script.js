/*
content script running on youtube.com
*/

console.log("running script.js");

let browserType = getBrowser();

setTimeout(function(){
    console.log("running setimeout")
    sendUrl();
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


function sendUrl() {
    console.log("run sendUrl from script.js");

    let payload = {
        "youtube": {
            "url": document.URL,
            "title": document.title
        }
    }
    console.log(JSON.stringify(payload));
    browserType.runtime.sendMessage(payload, function(response) {
        console.log(response.farewell);
    });

};
