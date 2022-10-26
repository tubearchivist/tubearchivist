'use strict';

/* global cast chrome getVideoPlayerVideoId postVideoProgress setProgressBar getVideoPlayer getVideoPlayerWatchStatus watchedThreshold isWatched getVideoData getURL getVideoPlayerCurrentTime */

function initializeCastApi() {
  cast.framework.CastContext.getInstance().setOptions({
    receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID, // Use built in receiver app on cast device, see https://developers.google.com/cast/docs/styled_receiver if you want to be able to add a theme, splash screen or watermark. Has a $5 one time fee.
    autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
  });

  let player = new cast.framework.RemotePlayer();
  let playerController = new cast.framework.RemotePlayerController(player);

  // Add event listerner to check if a connection to a cast device is initiated
  playerController.addEventListener(
    cast.framework.RemotePlayerEventType.IS_CONNECTED_CHANGED,
    function () {
      castConnectionChange(player);
    }
  );
  playerController.addEventListener(
    cast.framework.RemotePlayerEventType.CURRENT_TIME_CHANGED,
    function () {
      castVideoProgress(player);
    }
  );
  playerController.addEventListener(
    cast.framework.RemotePlayerEventType.IS_PAUSED_CHANGED,
    function () {
      castVideoPaused(player);
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

function castVideoProgress(player) {
  let videoId = getVideoPlayerVideoId();
  if (player.mediaInfo.contentId.includes(videoId)) {
    let currentTime = player.currentTime;
    let duration = player.duration;
    if (currentTime % 10 <= 1.0 && currentTime !== 0 && duration !== 0) {
      // Check progress every 10 seconds or else progress is checked a few times a second
      postVideoProgress(videoId, currentTime);
      setProgressBar(videoId, currentTime, duration);
      if (!getVideoPlayerWatchStatus()) {
        // Check if video is already marked as watched
        if (watchedThreshold(currentTime, duration)) {
          isWatched(videoId);
        }
      }
    }
  }
}

function castVideoPaused(player) {
  let videoId = getVideoPlayerVideoId();
  let currentTime = player.currentTime;
  let duration = player.duration;
  if (player.mediaInfo != null) {
    if (player.mediaInfo.contentId.includes(videoId)) {
      if (currentTime !== 0 && duration !== 0) {
        postVideoProgress(videoId, currentTime);
      }
    }
  }
}

function castStart() {
  let castSession = cast.framework.CastContext.getInstance().getCurrentSession();
  // Check if there is already media playing on the cast target to prevent recasting on page reload or switching to another video page
  if (!castSession.getMediaSession()) {
    let videoId = getVideoPlayerVideoId();
    let videoData = getVideoData(videoId);
    let contentId = getURL() + videoData.data.media_url;
    let contentTitle = videoData.data.title;
    let contentImage = getURL() + videoData.data.vid_thumb_url;

    let contentType = 'video/mp4'; // Set content type, only videos right now so it is hard coded
    let contentCurrentTime = getVideoPlayerCurrentTime(); // Get video's current position
    let contentActiveSubtitle = [];
    // Check if a subtitle is turned on.
    for (let i = 0; i < getVideoPlayer().textTracks.length; i++) {
      if (getVideoPlayer().textTracks[i].mode === 'showing') {
        contentActiveSubtitle = [i + 1];
      }
    }
    let contentSubtitles = [];
    let videoSubtitles = videoData.data.subtitles; // Array of subtitles
    if (typeof videoSubtitles !== 'undefined' && videoData.config.downloads.subtitle) {
      for (let i = 0; i < videoSubtitles.length; i++) {
        let subtitle = new chrome.cast.media.Track(i, chrome.cast.media.TrackType.TEXT);
        subtitle.trackContentId = videoSubtitles[i].media_url;
        subtitle.trackContentType = 'text/vtt';
        subtitle.subtype = chrome.cast.media.TextTrackType.SUBTITLES;
        subtitle.name = videoSubtitles[i].name;
        subtitle.language = videoSubtitles[i].lang;
        subtitle.customData = null;
        contentSubtitles.push(subtitle);
      }
    }

    let mediaInfo = new chrome.cast.media.MediaInfo(contentId, contentType); // Create MediaInfo var that contains url and content type
    // mediaInfo.streamType = chrome.cast.media.StreamType.BUFFERED; // Set type of stream, BUFFERED, LIVE, OTHER
    mediaInfo.metadata = new chrome.cast.media.GenericMediaMetadata(); // Create metadata var and add it to MediaInfo
    mediaInfo.metadata.title = contentTitle.replace('&amp;', '&'); // Set the video title
    mediaInfo.metadata.images = [new chrome.cast.Image(contentImage)]; // Set the video thumbnail
    // mediaInfo.textTrackStyle = new chrome.cast.media.TextTrackStyle();
    mediaInfo.tracks = contentSubtitles;

    let request = new chrome.cast.media.LoadRequest(mediaInfo); // Create request with the previously set MediaInfo.
    // request.queueData = new chrome.cast.media.QueueData(); // See https://developers.google.com/cast/docs/reference/web_sender/chrome.cast.media.QueueData for playlist support.
    request.currentTime = shiftCurrentTime(contentCurrentTime); // Set video start position based on the browser video position
    request.activeTrackIds = contentActiveSubtitle; // Set active subtitle based on video player
    // request.autoplay = false; // Set content to auto play, true by default
    castSession.loadMedia(request).then(
      function () {
        castSuccessful();
      },
      function (error) {
        castFailed(error.code);
      }
    ); // Send request to cast device
  }
}

function shiftCurrentTime(contentCurrentTime) {
  // Shift media back 3 seconds to prevent missing some of the content
  if (contentCurrentTime > 5) {
    return contentCurrentTime - 3;
  } else {
    return 0;
  }
}

function castSuccessful() {
  // console.log('Cast Successful.');
  getVideoPlayer().pause(); // Pause browser video on successful cast
}

function castFailed(errorCode) {
  console.log('Error code: ' + errorCode);
}

window['__onGCastApiAvailable'] = function (isAvailable) {
  if (isAvailable) {
    initializeCastApi();
  }
};
