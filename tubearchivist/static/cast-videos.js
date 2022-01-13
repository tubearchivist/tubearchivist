function initializeCastApi() {
    cast.framework.CastContext.getInstance().setOptions({
        receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,  // Use built in reciver app on cast device
        autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
    });

    var player = new cast.framework.RemotePlayer();
    var playerController = new cast.framework.RemotePlayerController(player);

    // Add event listerner to check if a connection to a cast device is initiated
    playerController.addEventListener(cast.framework.RemotePlayerEventType.IS_CONNECTED_CHANGED, 
        function () {
            castConnectionChange(player);
        }
    );
};

function castConnectionChange(player) {
    if (player.isConnected) { // If cast connection is intitialized start cast
        console.log("Cast Connected.");
        castStart();
    } else if (!player.isConnected) {
        console.log("Cast Disconnected.");
    }
}

function castStart() {
    var castSession = cast.framework.CastContext.getInstance().getCurrentSession();
    
    
    if (!castSession.getMediaSession()) { // Check if there is already media playing on the cast target to prevent recasting on page reload or switching to another video page
        contentId = document.getElementById("video-item").src; // Get URL from the video item
        contentTitle = document.getElementById('video-title').innerHTML; // Get Video title
        contentImage = document.getElementById("video-item").poster; // Get video thumbnail URL
        contentType = 'video/mp4'; // Set content type, only videos right now so it is hard coded

        mediaInfo = new chrome.cast.media.MediaInfo(contentId, contentType); // Create mediainfo var that contains url and content type
        mediaInfo.streamType = chrome.cast.media.StreamType.BUFFERED; // Set type of stream, in this case a normal video rather than a Livestream. I don't think this needs to be set sample code had it.
        mediaInfo.metadata = new chrome.cast.media.TvShowMediaMetadata(); // Create metadata var and add it to mediaInfo
        mediaInfo.metadata.title = contentTitle; // Set the video title
        mediaInfo.metadata.images = [{
            'url': contentImage // Set the thumbnail. IDK if this is working correctly, something to check later
        }];

        var request = new chrome.cast.media.LoadRequest(mediaInfo); // Create request
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

function castSuccessful() {
    console.log('Cast Successful.');
    document.getElementById("video-item").pause(); // Pause browser video on successful cast
}

function castFailed(errorCode) {
    console.log('Error code: ' + errorCode);
}

window['__onGCastApiAvailable'] = function(isAvailable) {
    if (isAvailable) {
        initializeCastApi();
    }
};
