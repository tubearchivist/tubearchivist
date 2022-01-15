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

})
