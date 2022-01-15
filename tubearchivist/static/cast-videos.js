function initializeCastApi() {
    cast.framework.CastContext.getInstance().setOptions({
        receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID, // Use built in reciver app on cast device, see https://developers.google.com/cast/docs/styled_receiver if you want to be able to add a theme, splash screen or watermark. Has a $5 one time fee.
        autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
    });

    var player = new cast.framework.RemotePlayer();
    var playerController = new cast.framework.RemotePlayerController(player);

    // Add event listerner to check if a connection to a cast device is initiated
    playerController.addEventListener(
        cast.framework.RemotePlayerEventType.IS_CONNECTED_CHANGED, function() { 
            castConnectionChange(player) 
        }
    );
}


function castConnectionChange(player) {
    // If cast connection is initialized start cast
    if (player.isConnected) {
        // console.log("Cast Connected.");
        castStart();
    } else if (!player.isConnected) {
        // console.log("Cast Disconnected.");
    }
}

function castStart() {
    var castSession = cast.framework.CastContext.getInstance().getCurrentSession();
    
    // Check if there is already media playing on the cast target to prevent recasting on page reload or switching to another video page
    if (!castSession.getMediaSession()) { 
        contentId = document.getElementById("video-item").src; // Get video URL
        contentTitle = document.getElementById('video-title').innerHTML; // Get video title
        contentImage = document.getElementById("video-item").poster; // Get video thumbnail URL
        contentType = 'video/mp4'; // Set content type, only videos right now so it is hard coded
        contentCurrentTime = document.getElementById("video-item").currentTime; // Get video's current position

        mediaInfo = new chrome.cast.media.MediaInfo(contentId, contentType); // Create MediaInfo var that contains url and content type
        // mediaInfo.streamType = chrome.cast.media.StreamType.BUFFERED; // Set type of stream, BUFFERED, LIVE, OTHER
        mediaInfo.metadata = new chrome.cast.media.GenericMediaMetadata(); // Create metadata var and add it to MediaInfo
        mediaInfo.metadata.title = contentTitle; // Set the video title
        mediaInfo.metadata.images = [new chrome.cast.Image(contentImage)]; // Set the video thumbnail

        var request = new chrome.cast.media.LoadRequest(mediaInfo); // Create request with the previously set MediaInfo. 
        // request.queueData = new chrome.cast.media.QueueData(); // See https://developers.google.com/cast/docs/reference/web_sender/chrome.cast.media.QueueData for playlist support.
        request.currentTime = shiftCurrentTime(contentCurrentTime); // Set video start position based on the browser video position
        // request.autoplay = false; // Set content to auto play, true by default
        castSession.loadMedia(request).then(
            function() { 
                castSuccessful();
            }, 
            function() { 
                castFailed(errorCode); 
            }
        ); // Send request to cast device
    }   
}

function shiftCurrentTime(contentCurrentTime) { // Shift media back 3 seconds to prevent missing some of the content
    if (contentCurrentTime > 5) {
        return(contentCurrentTime - 3);
    } else {
        return(0);
    }
}

function castSuccessful() {
    // console.log('Cast Successful.');
    document.getElementById("video-item").pause(); // Pause browser video on successful cast
}

function castFailed(errorCode) {
    console.log('Error code: ' + errorCode);
}

window['__onGCastApiAvailable'] = function(isAvailable) {
    if (isAvailable) {
        initializeCastApi();
    }
}
