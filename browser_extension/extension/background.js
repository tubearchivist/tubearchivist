/*
extension background script listening for events
*/

console.log("running background.js");

let browserType = getBrowser();


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


// send post request to API backend
async function sendPayload(url, token, payload) {

    const rawResponse = await fetch(url, {
        method: "POST",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": token,
            "mode": "no-cors"
        },
        body: JSON.stringify(payload)
    });

    const content = await rawResponse.json();
    return content;
}


// read access storage and send
function forwardRequest(payload) {

    console.log("running forwardRequest");

    function onGot(item) {
        console.log(item.access);

        const url = `${item.access.url}:${item.access.port}/api/download/`;
        console.log(`sending to ${url}`);
        const token = `Token ${item.access.apiKey}`;

        sendPayload(url, token, payload).then(content => {
            console.log(content);
        })

    };

    function onError(error) {
        console.local("failed to get access details");
        console.log(`Error: ${error}`);
    };

    browserType.storage.local.get("access", function(result) {
        onGot(result)
    });

}

// listen for messages
browserType.runtime.onMessage.addListener(
    function(request, sender, sendResponse) {
        console.log("responding from background.js listener");
        console.log(JSON.stringify(request));

        if (request.youtube) {
            browserType.storage.local.set(request, function() {
                console.log("Stored history: " + JSON.stringify(request));
            });
        } else if (request.download) {
            let payload = {
                "data": [
                    {
                        "youtube_id": request.download["url"],
                        "status": "pending",
                    }
                ]
            }
            console.log(payload);
            forwardRequest(payload);
        }
    }
);
