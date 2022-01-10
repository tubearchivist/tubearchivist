var session = null;

function initializeCastApi() {
        var applicationID = chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID;
        var sessionRequest = new chrome.cast.SessionRequest(applicationID);
        var apiConfig = new chrome.cast.ApiConfig(sessionRequest,
                sessionListener,
                receiverListener);
        chrome.cast.initialize(apiConfig, onInitSuccess, onInitError);
};

function sessionListener(e) {
        session = e;
        console.log('New session');
        if (session.media.length != 0) {
                console.log('Found ' + session.media.length + ' sessions.');
        }
}
 
function receiverListener(e) {
        if( e === 'available' ) {
                console.log("Chromecast was found on the network.");
        }
        else {
                console.log("There are no Chromecasts available.");
        }
}

function onInitSuccess() {
        console.log("Initialization succeeded");
}

function onInitError() {
        console.log("Initialization failed");
}

function startCast() {
        console.log("Starting cast...");
        chrome.cast.requestSession(onRequestSessionSuccess, onLaunchError);
}

function onRequestSessionSuccess(e) {
        console.log("Successfully created session: " + e.sessionId);
        session = e;
}

function onLaunchError() {
        console.log("Error connecting to the Chromecast.");
}

function onRequestSessionSuccess(e) {
        console.log("Successfully created session: " + e.sessionId);
        session = e;
        loadMedia();
}

function loadMedia() {
        if (!session) {
                console.log("No session.");
                return;
        }
        
        var videoSrc = document.getElementById("video-item").src;
        var mediaInfo = new chrome.cast.media.MediaInfo(videoSrc);
        mediaInfo.contentType = 'video/mp4';
  
        var request = new chrome.cast.media.LoadRequest(mediaInfo);
        request.autoplay = true;

        session.loadMedia(request, onLoadSuccess, onLoadError);
}

function onLoadSuccess() {
        console.log('Successfully loaded video.');
}

function onLoadError() {
        console.log('Failed to load video.');
}

function stopCast() {
        session.stop(onStopCastSuccess, onStopCastError);
}

function onStopCastSuccess() {
        console.log('Successfully stopped casting.');
}

function onStopCastError() {
        console.log('Error stopping cast.');
}
