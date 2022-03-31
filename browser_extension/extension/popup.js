/*
Loaded into popup index.html
*/

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

// store access details
document.getElementById("save-login").addEventListener("click", function () {
    console.log("save form");
    let toStore = {
        "access": {
            "url": document.getElementById("url").value,
            "port": document.getElementById("port").value,
            "apiKey": document.getElementById("api-key").value
        }
    };
    console.log(toStore);
    browserType.storage.local.set(toStore, function() {
        console.log("Stored connection details: " + JSON.stringify(toStore));
    });
})

// fill in form
document.addEventListener("DOMContentLoaded", async () => {

    console.log("executing dom loader");

    function onGot(item) {
        if (!item.access) {
            console.log("no access details found");
            return
        }
        console.log(item.access);
        document.getElementById("url").value = item.access.url;
        document.getElementById("port").value = item.access.port;
        document.getElementById("api-key").value = item.access.apiKey;
    };
    
    function onError(error) {
        console.log(`Error: ${error}`);
    };

    browserType.storage.local.get("access", function(result) {
        onGot(result)
    });

    browserType.storage.local.get("youtube", function(result) {
        downlodButton(result);
    })

})

function downlodButton(result) {
    console.log("running build dl button");
    let download = document.getElementById("download");
    let title = document.createElement("p");
    title.innerText = result.youtube.title;

    let button = document.createElement("button");
    button.innerText = "download";
    button.id = "downloadButton";
    button.setAttribute("data-id", result.youtube.url);

    button.addEventListener("click", function () {
        console.log("send download message");
        let payload = {
            "download": {
                "url": result.youtube.url
            }
        };
        browserType.runtime.sendMessage(payload);
    });

    download.appendChild(title);
    download.appendChild(button);
    download.appendChild(document.createElement("hr"));
}
