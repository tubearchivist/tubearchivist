initializeCastApi = function() {
    cast.framework.CastContext.getInstance().setOptions({
        receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID,
        autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED
    });

    var player = new cast.framework.RemotePlayer();
    var playerController = new cast.framework.RemotePlayerController(player);

    playerController.addEventListener(
        cast.framework.RemotePlayerEventType.IS_CONNECTED_CHANGED,
        function (e) {
            startCast(e.value);
        }.bind(this)
    );
};

startCast = function(value) {
    if (value) {

        var castSession = cast.framework.CastContext.getInstance().getCurrentSession();

        contentId = document.getElementById("video-item").src;
        contentTitle = document.getElementById('video-title').innerHTML;
        contentImage = document.getElementById("video-item").poster;
        contentType = 'video/mp4';

        mediaInfo = new chrome.cast.media.MediaInfo(contentId, contentType);
        mediaInfo.streamType = chrome.cast.media.StreamType.BUFFERED;
        mediaInfo.metadata = new chrome.cast.media.TvShowMediaMetadata();
        mediaInfo.metadata.title = contentTitle
        mediaInfo.metadata.images = [{
            'url': contentImage
        }];

        var request = new chrome.cast.media.LoadRequest(mediaInfo);
        castSession.loadMedia(request).then(
            function() { console.log('Load succeed'); },
            function(errorCode) { console.log('Error code: ' + errorCode); });
    }
}

window['__onGCastApiAvailable'] = function(isAvailable) {
    if (isAvailable) {
        initializeCastApi();
    }
};
