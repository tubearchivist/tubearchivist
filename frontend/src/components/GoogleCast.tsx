import { useCallback, useEffect, useState } from 'react';
import { VideoType } from '../pages/Home';
import updateVideoProgressById from '../api/actions/updateVideoProgressById';

const getURL = () => {
  return window.location.origin;
};

function shiftCurrentTime(contentCurrentTime: number | undefined) {
  console.log(contentCurrentTime);
  if (contentCurrentTime === undefined) {
    return 0;
  }

  // Shift media back 3 seconds to prevent missing some of the content
  if (contentCurrentTime > 5) {
    return contentCurrentTime - 3;
  } else {
    return 0;
  }
}

async function castVideoProgress(
  player: {
    mediaInfo: { contentId: string | string[] };
    currentTime: number;
    duration: number;
  },
  video: VideoType | undefined,
  onWatchStateChanged?: (status: boolean) => void,
) {
  if (!video) {
    console.log('castVideoProgress: Video to cast not found...');
    return;
  }
  const videoId = video.youtube_id;

  if (player.mediaInfo.contentId.includes(videoId)) {
    const currentTime = player.currentTime;
    const duration = player.duration;

    if (currentTime % 10 <= 1.0 && currentTime !== 0 && duration !== 0) {
      // Check progress every 10 seconds or else progress is checked a few times a second
      const videoProgressResponse = await updateVideoProgressById({
        youtubeId: videoId,
        currentProgress: currentTime,
      });

      if (videoProgressResponse.watched && video.player.watched !== videoProgressResponse.watched) {
        onWatchStateChanged?.(true);
      }
    }
  }
}

async function castVideoPaused(
  player: {
    currentTime: number;
    duration: number;
    mediaInfo: { contentId: string | string[] } | null;
  },
  video: VideoType | undefined,
) {
  if (!video) {
    console.log('castVideoPaused: Video to cast not found...');
    return;
  }

  const videoId = video?.youtube_id;

  const currentTime = player.currentTime;
  const duration = player.duration;

  if (player.mediaInfo != null) {
    if (player.mediaInfo.contentId.includes(videoId)) {
      if (currentTime !== 0 && duration !== 0) {
        await updateVideoProgressById({
          youtubeId: videoId,
          currentProgress: currentTime,
        });
      }
    }
  }
}

type GoogleCastProps = {
  video?: VideoType;
  setRefresh?: () => void;
  onWatchStateChanged?: (status: boolean) => void;
};

const GoogleCast = ({ video, setRefresh, onWatchStateChanged }: GoogleCastProps) => {
  const [isConnected, setIsConnected] = useState(false);

  const setup = useCallback(() => {
    const cast = globalThis.cast;
    const chrome = globalThis.chrome;

    cast.framework.CastContext.getInstance().setOptions({
      receiverApplicationId: chrome.cast.media.DEFAULT_MEDIA_RECEIVER_APP_ID, // Use built in receiver app on cast device, see https://developers.google.com/cast/docs/styled_receiver if you want to be able to add a theme, splash screen or watermark. Has a $5 one time fee.
      autoJoinPolicy: chrome.cast.AutoJoinPolicy.ORIGIN_SCOPED,
    });

    const player = new cast.framework.RemotePlayer();

    const playerController = new cast.framework.RemotePlayerController(player);

    // Add event listerner to check if a connection to a cast device is initiated
    playerController.addEventListener(
      cast.framework.RemotePlayerEventType.IS_CONNECTED_CHANGED,
      function () {
        setIsConnected(player.isConnected);
      },
    );

    playerController.addEventListener(
      cast.framework.RemotePlayerEventType.CURRENT_TIME_CHANGED,
      function () {
        castVideoProgress(player, video, onWatchStateChanged);
      },
    );

    playerController.addEventListener(
      cast.framework.RemotePlayerEventType.IS_PAUSED_CHANGED,
      function () {
        castVideoPaused(player, video);
        setRefresh?.();
      },
    );

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setRefresh, video]);

  const startPlayback = useCallback(() => {
    const chrome = globalThis.chrome;
    const cast = globalThis.cast;
    const castSession = cast.framework.CastContext.getInstance().getCurrentSession();

    const mediaUrl = video?.media_url;
    const vidThumbUrl = video?.vid_thumb_url;
    const contentTitle = video?.title;
    const contentId = `${getURL()}${mediaUrl}`;
    const contentImage = `${getURL()}${vidThumbUrl}`;
    const contentType = 'video/mp4'; // Set content type, only videos right now so it is hard coded

    const contentSubtitles = [];
    const videoSubtitles = video?.subtitles; // Array of subtitles
    if (typeof videoSubtitles !== 'undefined') {
      for (let i = 0; i < videoSubtitles.length; i++) {
        const subtitle = new chrome.cast.media.Track(i, chrome.cast.media.TrackType.TEXT);

        subtitle.trackContentId = videoSubtitles[i].media_url;
        subtitle.trackContentType = 'text/vtt';
        subtitle.subtype = chrome.cast.media.TextTrackType.SUBTITLES;
        subtitle.name = videoSubtitles[i].name;
        subtitle.language = videoSubtitles[i].lang;
        subtitle.customData = null;

        contentSubtitles.push(subtitle);
      }
    }

    const mediaInfo = new chrome.cast.media.MediaInfo(contentId, contentType); // Create MediaInfo var that contains url and content type
    // mediaInfo.streamType = chrome.cast.media.StreamType.BUFFERED; // Set type of stream, BUFFERED, LIVE, OTHER
    mediaInfo.metadata = new chrome.cast.media.GenericMediaMetadata(); // Create metadata var and add it to MediaInfo
    mediaInfo.metadata.title = contentTitle?.replace('&amp;', '&'); // Set the video title
    mediaInfo.metadata.images = [new chrome.cast.Image(contentImage)]; // Set the video thumbnail
    // mediaInfo.textTrackStyle = new chrome.cast.media.TextTrackStyle();
    mediaInfo.tracks = contentSubtitles;

    const request = new chrome.cast.media.LoadRequest(mediaInfo); // Create request with the previously set MediaInfo.
    // request.queueData = new chrome.cast.media.QueueData(); // See https://developers.google.com/cast/docs/reference/web_sender/chrome.cast.media.QueueData for playlist support.
    request.currentTime = shiftCurrentTime(video?.player?.position); // Set video start position based on the browser video position
    // request.activeTrackIds = contentActiveSubtitle; // Set active subtitle based on video player

    castSession.loadMedia(request).then(
      function () {
        console.log('media loaded');
      },
      function (error: { code: string }) {
        console.log('Error', error, 'Error code: ' + error.code);
      },
    ); // Send request to cast device

    // Do not add videoProgress?.position, this will cause loops!
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [video?.media_url, video?.subtitles, video?.title, video?.vid_thumb_url]);

  useEffect(() => {
    // @ts-expect-error __onGCastApiAvailable is the google cast window hook ( source: https://developers.google.com/cast/docs/web_sender/integrate )
    window['__onGCastApiAvailable'] = function (isAvailable: boolean) {
      if (isAvailable) {
        setup();
      }
    };
  }, [setup]);

  useEffect(() => {
    console.log('isConnected', isConnected);
    if (isConnected) {
      startPlayback();
    }
  }, [isConnected, startPlayback]);

  if (!video) {
    return <p>Video for cast not found...</p>;
  }

  return (
    <>
      <>
        <script
          type="text/javascript"
          src="https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1"
        ></script>

        {/* @ts-expect-error React does not know what to do with the google-cast-launcher, but it works. */}
        <google-cast-launcher id="castbutton"></google-cast-launcher>
      </>
    </>
  );
};

export default GoogleCast;
