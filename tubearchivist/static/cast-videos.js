initializeCastApi = function() {
    cast.framework.CastContext.getInstance().setOptions({
        receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,  // Use built in reciver app on cast device
        autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
    });

    var player = new cast.framework.RemotePlayer();
    var playerController = new cast.framework.RemotePlayerController(player);

    playerController.addEventListener( // Add event listerner to check if a connection to a cast device is initiated.
        cast.framework.RemotePlayerEventType.IS_CONNECTED_CHANGED,
        function (e) {
            startCast(e.value);
        }.bind(this)
    );
};

startCast = function(value) { // If a device is selected and a connection is made send current video to cast device
    if (value) {

        var castSession = cast.framework.CastContext.getInstance().getCurrentSession();

        contentId = document.getElementById("video-item").src; // Get URL from the video item
        contentTitle = document.getElementById('video-title').innerHTML; // Get Video title
        contentImage = document.getElementById("video-item").poster; // Get video thumbnail URL
        contentType = 'video/mp4'; // Set content type, only videos right now so it is hard coded

        mediaInfo = new chrome.cast.media.MediaInfo(contentId, contentType); // Create mediainfo var that contains url and content type
        mediaInfo.streamType = chrome.cast.media.StreamType.BUFFERED; // Set type of stream, in this case a normal video rather than a Livestream. I don't think this needs to be set sample code had it.
        mediaInfo.metadata = new chrome.cast.media.TvShowMediaMetadata(); // Create metadata var and add it to mediaInfo
        mediaInfo.metadata.title = contentTitle; // Set the video title
        mediaInfo.metadata.images = [{
            'url': contentImage 
        }]; // Set the thumbnail. IDK if this is working correctly, something to check later

        var request = new chrome.cast.media.LoadRequest(mediaInfo); // Create request
        castSession.loadMedia(request).then(
            function() { console.log('Load succeed'); },
            function(errorCode) { console.log('Error code: ' + errorCode); }); // Send request to cast device
    }
}

window['__onGCastApiAvailable'] = function(isAvailable) {
    if (isAvailable) {
        initializeCastApi();
    }
};
