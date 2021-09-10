/**
 * Handle progress bar on /download
 * 
 */


setTimeout(function(){
    checkMessage();
}, 1000);

// initial check for messages
function checkMessage() {
    var req = new XMLHttpRequest();
    req.responseType = 'json';
    req.open('GET', '/downloads/progress', true);
    req.onload = function() {
        var dlProgress = req.response;
        if (dlProgress['status']) {
            console.log('start interval');
            buildDownloadMessage(dlProgress);
            handleInterval();
        };
        console.log(JSON.stringify(dlProgress));
    };
    req.send();
}

// set interval until no more messages
function handleInterval() {
    var watchDownload = setInterval(function() {
        var req = new XMLHttpRequest();
        req.responseType = 'json';
        req.open('GET', '/downloads/progress', true);
        req.onload = function() {
            var dlProgress = req.response;
            if (dlProgress['status']) {
                console.log('continue interval');
                buildDownloadMessage(dlProgress);
            } else {
                console.log('stop interval');
                clearInterval(watchDownload);
                location.reload();
            };
            console.log(JSON.stringify(dlProgress));
        };
        req.send();
    }, 3000);
};

// remove and set message
function buildDownloadMessage(dlProgress) {
    var box = document.getElementById('downloadMessage');
    box.innerHTML = '';
    var dlStatus = dlProgress['status'];
    var dlTitle = dlProgress['title'];
    var dlMessage = dlProgress['message'];
    var dlLevel = dlProgress['level'];
    // animate
    if (dlStatus === 'rescan') {
        animate('rescan-icon', 'rotate-img');
    } else if (dlStatus === 'downloading') {
        animate('download-icon', 'bounce-img');
    };
    // div box
    var box = document.getElementById('downloadMessage');
    var message = document.createElement('div');
    message.classList.add('download-progress');
    message.classList.add(dlLevel);
    message.id = 'progress';
    message.setAttribute('data', dlStatus);
    var title = document.createElement('h3');
    title.innerHTML = dlTitle;
    var messageText = document.createElement('p');
    messageText.innerHTML = dlMessage;
    message.appendChild(title);
    message.appendChild(messageText);
    box.appendChild(message);
};

function animate(elementId, animationClass) {
    var toAnimate = document.getElementById(elementId);
    if (toAnimate.className !== animationClass) {
        toAnimate.className = animationClass;
        console.log(elementId, animationClass);
    }
}
