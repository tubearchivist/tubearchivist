/**
 * Handle multi channel notifications
 * 
 */

checkMessages()

// page map to notification status
const messageTypes = {
    "download": ["message:download", "message:add", "message:rescan", "message:playlistscan"],
    "channel": ["message:subchannel"],
    "channel_id": ["message:playlistscan"],
    "playlist": ["message:subplaylist"],
    "setting": ["message:setting"]
}

// start to look for messages
function checkMessages() {
    var notifications = document.getElementById("notifications");
    if (notifications) {
        var dataOrigin = notifications.getAttribute("data");
        getMessages(dataOrigin);
    }
}

// get messages for page on timer
function getMessages(dataOrigin) {
    fetch('/progress/').then(response => {
        return response.json();
    }).then(responseData => {
        var messages = buildMessage(responseData, dataOrigin);
        if (messages.length > 0) {
            // restart itself
            setTimeout(function() {
                getMessages(dataOrigin);
            }, 3000);
        };
    });
}

// make div for all messages, return relevant
function buildMessage(responseData, dataOrigin) {
    // filter relevan messages
    var allMessages = responseData["messages"];
    var messages = allMessages.filter(function(value) {
        return messageTypes[dataOrigin].includes(value["status"])
    }, dataOrigin);
    // build divs
    var notificationDiv = document.getElementById("notifications");
    var nots = notificationDiv.childElementCount;
    notificationDiv.innerHTML = "";
    for (let i = 0; i < messages.length; i++) {
        var messageData = messages[i];
        var messageStatus = messageData["status"];
        var messageBox = document.createElement("div");
        var title = document.createElement("h3");
        title.innerHTML = messageData["title"];
        var message = document.createElement("p");
        message.innerHTML = messageData["message"];
        messageBox.appendChild(title);
        messageBox.appendChild(message);
        messageBox.classList.add(messageData["level"], "notification");
        notificationDiv.appendChild(messageBox);
        if (messageStatus === "message:download") {
            checkDownloadIcons();
        };
    };
    // reload page when no more notifications
    if (nots > 0 && messages.length === 0) {
        location.reload();
    };
    return messages
}

// check if download icons are needed
function checkDownloadIcons() {
    var iconBox = document.getElementById("downloadControl");
    if (iconBox.childElementCount === 0) {
        var downloadIcons = buildDownloadIcons();
        iconBox.appendChild(downloadIcons);
    };
}

// add dl control icons
function buildDownloadIcons() {
    var downloadIcons = document.createElement('div');
    downloadIcons.classList = 'dl-control-icons';
    // stop icon
    var stopIcon = document.createElement('img');
    stopIcon.setAttribute('id', "stop-icon");
    stopIcon.setAttribute('title', "Stop Download Queue");
    stopIcon.setAttribute('src', "/static/img/icon-stop.svg");
    stopIcon.setAttribute('alt', "stop icon");
    stopIcon.setAttribute('onclick', 'stopQueue()');
    // kill icon
    var killIcon = document.createElement('img');
    killIcon.setAttribute('id', "kill-icon");
    killIcon.setAttribute('title', "Kill Download Queue");
    killIcon.setAttribute('src', "/static/img/icon-close.svg");
    killIcon.setAttribute('alt', "kill icon");
    killIcon.setAttribute('onclick', 'killQueue()');
    // stich together
    downloadIcons.appendChild(stopIcon);
    downloadIcons.appendChild(killIcon);
    return downloadIcons
}
