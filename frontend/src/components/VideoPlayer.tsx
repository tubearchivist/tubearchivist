import updateVideoProgressById from '../api/actions/updateVideoProgressById';
import { SponsorBlockSegmentType, SponsorBlockType, VideoResponseType } from '../pages/Video';
import {
  Dispatch,
  Fragment,
  SetStateAction,
  SyntheticEvent,
  useEffect,
  useRef,
  useState,
} from 'react';
import formatTime from '../functions/formatTime';
import { useSearchParams } from 'react-router-dom';
import getApiUrl from '../configuration/getApiUrl';
import { useKeyPress } from '../functions/useKeypressHook';

const VIDEO_PLAYBACK_SPEEDS = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3];

type VideoTag = SyntheticEvent<HTMLVideoElement, Event>;

export type SkippedSegmentType = {
  from: number;
  to: number;
};

export type SponsorSegmentsSkippedType = Record<string, SkippedSegmentType>;

type Subtitle = {
  name: string;
  source: string;
  lang: string;
  media_url: string;
};

type SubtitlesProp = {
  subtitles: Subtitle[];
};

const Subtitles = ({ subtitles }: SubtitlesProp) => {
  return subtitles.map((subtitle: Subtitle) => {
    let label = subtitle.name;

    if (subtitle.source === 'auto') {
      label += ' - auto';
    }

    return (
      <track
        key={subtitle.name}
        label={label}
        kind="subtitles"
        srcLang={subtitle.lang}
        src={`${getApiUrl()}${subtitle.media_url}`}
      />
    );
  });
};

const handleTimeUpdate =
  (
    youtubeId: string,
    duration: number,
    watched: boolean,
    sponsorBlock?: SponsorBlockType,
    setSponsorSegmentSkipped?: Dispatch<SetStateAction<SponsorSegmentsSkippedType>>,
    onWatchStateChanged?: (status: boolean) => void,
  ) =>
  async (videoTag: VideoTag) => {
    const currentTime = Number(videoTag.currentTarget.currentTime);

    if (sponsorBlock && sponsorBlock.segments) {
      sponsorBlock.segments.forEach((segment: SponsorBlockSegmentType) => {
        const [from, to] = segment.segment;

        if (currentTime >= from && currentTime <= from + 0.3) {
          videoTag.currentTarget.currentTime = to;

          setSponsorSegmentSkipped?.((segments: SponsorSegmentsSkippedType) => {
            return { ...segments, [segment.UUID]: { from, to } };
          });
        }

        if (currentTime > to + 10) {
          setSponsorSegmentSkipped?.((segments: SponsorSegmentsSkippedType) => {
            return { ...segments, [segment.UUID]: { from: 0, to: 0 } };
          });
        }
      });
    }

    if (currentTime < 10 && currentTime === Number(videoTag.currentTarget.duration)) return;
    if (Number((currentTime % 10).toFixed(1)) <= 0.2) {
      // Check progress every 10 seconds or else progress is checked a few times a second
      const videoProgressResponse = await updateVideoProgressById({
        youtubeId,
        currentProgress: currentTime,
      });

      if (videoProgressResponse.watched && watched !== videoProgressResponse.watched) {
        onWatchStateChanged?.(true);
      }
    }
  };

type VideoPlayerProps = {
  video: VideoResponseType;
  sponsorBlock?: SponsorBlockType;
  embed?: boolean;
  autoplay?: boolean;
  onWatchStateChanged?: (status: boolean) => void;
  onVideoEnd?: () => void;
};

const VideoPlayer = ({
  video,
  sponsorBlock,
  embed,
  autoplay = false,
  onWatchStateChanged,
  onVideoEnd,
}: VideoPlayerProps) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const [searchParams] = useSearchParams();
  const searchParamVideoProgress = searchParams.get('t');

  const [skippedSegments, setSkippedSegments] = useState<SponsorSegmentsSkippedType>({});
  const [isMuted, setIsMuted] = useState(false);
  const [playbackSpeedIndex, setPlaybackSpeedIndex] = useState(3);
  const [lastSubtitleTack, setLastSubtitleTack] = useState(0);
  const [showHelpDialog, setShowHelpDialog] = useState(false);
  const [showInfoDialog, setShowInfoDialog] = useState(false);
  const [infoDialogContent, setInfoDialogContent] = useState('');

  const questionmarkPressed = useKeyPress('?');
  const mutePressed = useKeyPress('m');
  const fullscreenPressed = useKeyPress('f');
  const subtitlesPressed = useKeyPress('c');
  const increasePlaybackSpeedPressed = useKeyPress('>');
  const decreasePlaybackSpeedPressed = useKeyPress('<');
  const resetPlaybackSpeedPressed = useKeyPress('=');
  const arrowRightPressed = useKeyPress('ArrowRight');
  const arrowLeftPressed = useKeyPress('ArrowLeft');

  const videoId = video.data.youtube_id;
  const videoUrl = video.data.media_url;
  const videoThumbUrl = video.data.vid_thumb_url;
  const watched = video.data.player.watched;
  const duration = video.data.player.duration;
  const videoSubtitles = video.data.subtitles;

  let videoSrcProgress =
    Number(video.data.player?.position) > 0 ? Number(video.data.player?.position) : '';

  if (searchParamVideoProgress !== null) {
    videoSrcProgress = searchParamVideoProgress;
  }

  const infoDialog = (content: string) => {
    setInfoDialogContent(content);
    setShowInfoDialog(true);

    setTimeout(() => {
      setShowInfoDialog(false);
      setInfoDialogContent('');
    }, 500);
  };

  const handleVideoEnd =
    (
      youtubeId: string,
      watched: boolean,
      setSponsorSegmentSkipped?: Dispatch<SetStateAction<SponsorSegmentsSkippedType>>,
    ) =>
    async (videoTag: VideoTag) => {
      const currentTime = Number(videoTag.currentTarget.currentTime);

      const videoProgressResponse = await updateVideoProgressById({
        youtubeId,
        currentProgress: currentTime,
      });

      if (videoProgressResponse.watched && watched !== videoProgressResponse.watched) {
        onWatchStateChanged?.(true);
      }

      setSponsorSegmentSkipped?.((segments: SponsorSegmentsSkippedType) => {
        const keys = Object.keys(segments);

        keys.forEach(uuid => {
          segments[uuid] = { from: 0, to: 0 };
        });

        return segments;
      });

      onVideoEnd?.();
    };

  useEffect(() => {
    if (mutePressed) {
      setIsMuted(!isMuted);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mutePressed]);

  useEffect(() => {
    if (increasePlaybackSpeedPressed) {
      const newSpeed = playbackSpeedIndex + 1;

      if (videoRef.current && VIDEO_PLAYBACK_SPEEDS[newSpeed]) {
        const speed = VIDEO_PLAYBACK_SPEEDS[newSpeed];
        videoRef.current.playbackRate = speed;

        setPlaybackSpeedIndex(newSpeed);
        infoDialog(`${speed}x`);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [increasePlaybackSpeedPressed]);

  useEffect(() => {
    if (decreasePlaybackSpeedPressed) {
      const newSpeedIndex = playbackSpeedIndex - 1;

      if (videoRef.current && VIDEO_PLAYBACK_SPEEDS[newSpeedIndex]) {
        const speed = VIDEO_PLAYBACK_SPEEDS[newSpeedIndex];
        videoRef.current.playbackRate = speed;

        setPlaybackSpeedIndex(newSpeedIndex);
        infoDialog(`${speed}x`);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [decreasePlaybackSpeedPressed]);

  useEffect(() => {
    if (resetPlaybackSpeedPressed) {
      const newSpeedIndex = 3;

      if (videoRef.current && VIDEO_PLAYBACK_SPEEDS[newSpeedIndex]) {
        const speed = VIDEO_PLAYBACK_SPEEDS[newSpeedIndex];
        videoRef.current.playbackRate = speed;

        setPlaybackSpeedIndex(newSpeedIndex);
        infoDialog(`${speed}x`);
      }
    }
  }, [resetPlaybackSpeedPressed]);

  useEffect(() => {
    if (fullscreenPressed) {
      if (videoRef.current && videoRef.current.requestFullscreen && !document.fullscreenElement) {
        videoRef.current.requestFullscreen().catch(e => {
          console.error(e);
          infoDialog('Unable to enter fullscreen');
        });
      } else {
        document.exitFullscreen().catch(e => {
          console.error(e);
          infoDialog('Unable to exit fullscreen');
        });
      }
    }
  }, [fullscreenPressed]);

  useEffect(() => {
    if (subtitlesPressed) {
      if (videoRef.current) {
        const tracks = [...videoRef.current.textTracks];

        if (tracks.length === 0) {
          return;
        }

        const lastIndex = tracks.findIndex(x => x.mode === 'showing');
        const active = tracks[lastIndex];

        if (!active && lastSubtitleTack !== 0) {
          tracks[lastSubtitleTack - 1].mode = 'showing';
        } else {
          if (active) {
            active.mode = 'hidden';

            setLastSubtitleTack(lastIndex + 1);
          }
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subtitlesPressed]);

  useEffect(() => {
    if (arrowLeftPressed) {
      infoDialog('- 5 seconds');
    }
  }, [arrowLeftPressed]);

  useEffect(() => {
    if (arrowRightPressed) {
      infoDialog('+ 5 seconds');
    }
  }, [arrowRightPressed]);

  useEffect(() => {
    if (questionmarkPressed) {
      if (!showHelpDialog) {
        setTimeout(() => {
          setShowHelpDialog(false);
        }, 3000);
      }

      setShowHelpDialog(!showHelpDialog);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [questionmarkPressed]);

  return (
    <>
      <div id="player" className={embed ? '' : 'player-wrapper'}>
        <div className={embed ? '' : 'video-main'}>
          <video
            ref={videoRef}
            key={`${getApiUrl()}${videoUrl}`}
            poster={`${getApiUrl()}${videoThumbUrl}`}
            onVolumeChange={(videoTag: VideoTag) => {
              localStorage.setItem('playerVolume', videoTag.currentTarget.volume.toString());
            }}
            onRateChange={(videoTag: VideoTag) => {
              localStorage.setItem('playerSpeed', videoTag.currentTarget.playbackRate.toString());
            }}
            onLoadStart={(videoTag: VideoTag) => {
              videoTag.currentTarget.volume = Number(localStorage.getItem('playerVolume') ?? 1);
              videoTag.currentTarget.playbackRate = Number(
                localStorage.getItem('playerSpeed') ?? 1,
              );
            }}
            onTimeUpdate={handleTimeUpdate(
              videoId,
              duration,
              watched,
              sponsorBlock,
              setSkippedSegments,
              onWatchStateChanged,
            )}
            onPause={async (videoTag: VideoTag) => {
              const currentTime = Number(videoTag.currentTarget.currentTime);

              if (currentTime < 10 || currentTime > duration * 0.95) return;

              await updateVideoProgressById({
                youtubeId: videoId,
                currentProgress: currentTime,
              });
            }}
            onEnded={handleVideoEnd(videoId, watched)}
            autoPlay={autoplay}
            controls
            width="100%"
            playsInline
            id="video-item"
            muted={isMuted}
          >
            <source
              src={`${getApiUrl()}${videoUrl}#t=${videoSrcProgress}`}
              type="video/mp4"
              id="video-source"
            />
            {videoSubtitles && <Subtitles subtitles={videoSubtitles} />}
          </video>
        </div>
      </div>

      <dialog className="video-modal" open={showHelpDialog}>
        <div className="video-modal-text">
          <table className="video-modal-table">
            <tbody>
              <tr>
                <td>Show help</td>
                <td>?</td>
              </tr>
              <tr>
                <td>Toggle mute</td>
                <td>m</td>
              </tr>
              <tr>
                <td>Toggle fullscreen</td>
                <td>f</td>
              </tr>
              <tr>
                <td>Toggle subtitles (if available)</td>
                <td>c</td>
              </tr>
              <tr>
                <td>Increase speed</td>
                <td>&gt;</td>
              </tr>
              <tr>
                <td>Decrease speed</td>
                <td>&lt;</td>
              </tr>
              <tr>
                <td>Reset speed</td>
                <td>=</td>
              </tr>
              <tr>
                <td>Back 5 seconds</td>
                <td>←</td>
              </tr>
              <tr>
                <td>Forward 5 seconds</td>
                <td>→</td>
              </tr>
            </tbody>
          </table>

          <form className="video-modal-form" method="dialog">
            <button>Close</button>
          </form>
        </div>
      </dialog>

      <dialog className="video-modal" open={showInfoDialog}>
        <div className="video-modal-text">{infoDialogContent}</div>
      </dialog>

      <div className="sponsorblock" id="sponsorblock">
        {sponsorBlock?.is_enabled && (
          <>
            {sponsorBlock.segments.length == 0 && (
              <h4>
                This video doesn't have any sponsor segments added. To add a segment go to{' '}
                <u>
                  <a href={`https://www.youtube.com/watch?v=${videoId}`}>this video on YouTube</a>
                </u>{' '}
                and add a segment using the{' '}
                <u>
                  <a href="https://sponsor.ajay.app/">SponsorBlock</a>
                </u>{' '}
                extension.
              </h4>
            )}
            {sponsorBlock.has_unlocked && (
              <h4>
                This video has unlocked sponsor segments. Go to{' '}
                <u>
                  <a href={`https://www.youtube.com/watch?v=${videoId}`}>this video on YouTube</a>
                </u>{' '}
                and vote on the segments using the{' '}
                <u>
                  <a href="https://sponsor.ajay.app/">SponsorBlock</a>
                </u>{' '}
                extension.
              </h4>
            )}

            {Object.values(skippedSegments).map(({ from, to }, index) => {
              return (
                <Fragment key={`${from}-${to}-${index}`}>
                  {from !== 0 && to !== 0 && (
                    <h3>
                      Skipped sponsor segment from {formatTime(from)} to {formatTime(to)}.
                    </h3>
                  )}
                </Fragment>
              );
            })}
          </>
        )}
      </div>
    </>
  );
};

export default VideoPlayer;
