import updateVideoProgressById from '../api/actions/updateVideoProgressById';
import { SponsorBlockSegmentType, SponsorBlockType } from '../pages/Video';
import {
  Dispatch,
  Fragment,
  KeyboardEvent,
  SetStateAction,
  SyntheticEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import formatTime from '../functions/formatTime';
import { useSearchParams } from 'react-router-dom';
import getApiUrl from '../configuration/getApiUrl';
import { useKeyPress } from '../functions/useKeypressHook';
import { VideoResponseType } from '../api/loader/loadVideoById';

const VIDEO_PLAYBACK_SPEEDS = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75, 3];

type VideoTag = SyntheticEvent<HTMLVideoElement, Event>;
type AudioTag = SyntheticEvent<HTMLAudioElement, Event>;

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
    watched: boolean,
    sponsorBlock?: SponsorBlockType,
    setSponsorSegmentSkipped?: Dispatch<SetStateAction<SponsorSegmentsSkippedType>>,
    onWatchStateChanged?: (status: boolean) => void,
  ) =>
  async (videoTag: VideoTag) => {
    const currentTime = Number(videoTag.currentTarget.currentTime);

    if (sponsorBlock && sponsorBlock.segments) {
      sponsorBlock.segments.forEach((segment: SponsorBlockSegmentType) => {
        const actionType = segment.actionType;
        const doSkip = actionType == 'skip';
        const [from, to] = segment.segment;

        if (doSkip && currentTime >= from && currentTime <= from + 0.3) {
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

      const { data: videoProgressResponseData } = videoProgressResponse ?? {};

      if (videoProgressResponseData?.watched && watched !== videoProgressResponseData.watched) {
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
  seekToTimestamp?: number;
  setSeekToTimestamp?: (timestamp: number | undefined) => void;
};

const VideoPlayer = ({
  video,
  sponsorBlock,
  embed,
  autoplay = false,
  onWatchStateChanged,
  onVideoEnd,
  seekToTimestamp,
  setSeekToTimestamp,
}: VideoPlayerProps) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [audioMode, setAudioMode] = useState(localStorage.getItem('playerAudioMode') === 'true');

  // Returns the currently active media element regardless of mode
  const mediaRef = (): HTMLVideoElement | HTMLAudioElement | null =>
    audioMode ? audioRef.current : videoRef.current;

  const toggleAudioMode = (next: boolean) => {
    localStorage.setItem('playerAudioMode', String(next));
    setAudioMode(next);
  };

  useEffect(() => {
    if (seekToTimestamp === undefined || !videoRef.current) {
      return;
    }

    const videoDuration = videoRef.current.duration;
    if (isNaN(videoDuration) || seekToTimestamp > videoDuration) {
      return;
    }

    videoRef.current.currentTime = seekToTimestamp;

    if (videoRef.current.paused) {
      videoRef.current.play();
    }
    if (setSeekToTimestamp) setSeekToTimestamp(undefined);
    window.scroll(0, 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seekToTimestamp]);

  const [searchParams] = useSearchParams();
  const searchParamVideoProgress = searchParams.get('t');

  const volumeFromStorage = Number(localStorage.getItem('playerVolume') ?? 1);
  const playBackSpeedFromStorage = Number(localStorage.getItem('playerSpeed') || 1);
  const playBackSpeedIndex =
    VIDEO_PLAYBACK_SPEEDS.indexOf(playBackSpeedFromStorage) !== -1
      ? VIDEO_PLAYBACK_SPEEDS.indexOf(playBackSpeedFromStorage)
      : 3;

  const [skippedSegments, setSkippedSegments] = useState<SponsorSegmentsSkippedType>({});
  const [isMuted, setIsMuted] = useState(false);
  const [playbackSpeedIndex, setPlaybackSpeedIndex] = useState(playBackSpeedIndex);
  const [lastSubtitleTack, setLastSubtitleTack] = useState(0);
  const [showHelpDialog, setShowHelpDialog] = useState(false);
  const [showInfoDialog, setShowInfoDialog] = useState(false);
  const [infoDialogContent, setInfoDialogContent] = useState('');
  const [isTheaterMode, setIsTheaterMode] = useState(false);

  const videoId = video.youtube_id;
  const videoUrl = video.media_url;
  const videoThumbUrl = video.vid_thumb_url;
  const watched = video.player.watched;
  const duration = video.player.duration;
  const videoSubtitles = video.subtitles;

  let videoSrcProgress = Number(video.player?.position) > 0 ? Number(video.player?.position) : '';

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

  useKeyPress('m', () => {
    setIsMuted(current => !current);
  });

  useKeyPress('p', () => {
    const media = mediaRef();
    if (media?.paused) {
      media.play();
    } else {
      media?.pause();
    }
  });

  useKeyPress('>', () => {
    const newSpeed = playbackSpeedIndex + 1;
    const media = mediaRef();

    if (media && VIDEO_PLAYBACK_SPEEDS[newSpeed]) {
      const speed = VIDEO_PLAYBACK_SPEEDS[newSpeed];
      media.playbackRate = speed;

      setPlaybackSpeedIndex(newSpeed);
      infoDialog(`${speed}x`);
    }
  });

  useKeyPress('<', () => {
    const newSpeedIndex = playbackSpeedIndex - 1;
    const media = mediaRef();

    if (media && VIDEO_PLAYBACK_SPEEDS[newSpeedIndex]) {
      const speed = VIDEO_PLAYBACK_SPEEDS[newSpeedIndex];
      media.playbackRate = speed;

      setPlaybackSpeedIndex(newSpeedIndex);
      infoDialog(`${speed}x`);
    }
  });

  useKeyPress('=', () => {
    const newSpeedIndex = 3;
    const media = mediaRef();

    if (media && VIDEO_PLAYBACK_SPEEDS[newSpeedIndex]) {
      const speed = VIDEO_PLAYBACK_SPEEDS[newSpeedIndex];
      media.playbackRate = speed;

      setPlaybackSpeedIndex(newSpeedIndex);
      infoDialog(`${speed}x`);
    }
  });

  useKeyPress('f', () => {
    if (audioMode) return;
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
  });

  useKeyPress('c', () => {
    if (audioMode || !videoRef.current) return;

    const tracks = [...videoRef.current.textTracks];
    if (tracks.length === 0) return;

    const lastIndex = tracks.findIndex(x => x.mode === 'showing');
    const active = tracks[lastIndex];

    if (!active && lastSubtitleTack !== 0) {
      tracks[lastSubtitleTack - 1].mode = 'showing';
    } else if (active) {
      active.mode = 'hidden';

      setLastSubtitleTack(lastIndex + 1);
    }
  });

  useKeyPress('ArrowLeft', () => {
    const media = mediaRef();
    if (media?.currentTime !== undefined) {
      infoDialog('- 5 seconds');
      media.currentTime -= 5;
    }
  });

  useKeyPress('ArrowRight', () => {
    const media = mediaRef();
    if (media?.currentTime !== undefined) {
      infoDialog('+ 5 seconds');
      media.currentTime += 5;
    }
  });

  useKeyPress('?', () => {
    setShowHelpDialog(current => {
      const next = !current;

      if (next) {
        setTimeout(() => {
          setShowHelpDialog(false);
        }, 3000);
      }

      return next;
    });
  });

  useKeyPress('t', () => {
    if (embed) {
      return;
    }

    setIsTheaterMode(current => {
      const next = !current;
      infoDialog(next ? 'Theater mode' : 'Normal mode');

      return next;
    });
  });

  useKeyPress('Escape', () => {
    if (embed) {
      return;
    }

    setIsTheaterMode(current => {
      if (!current) {
        return current;
      }

      infoDialog('Normal mode');

      return false;
    });
  });

  const handleVolumeChange = useCallback((e: VideoTag | AudioTag) => {
    localStorage.setItem('playerVolume', e.currentTarget.volume.toString());
  }, []);

  const handleRateChange = useCallback((e: VideoTag | AudioTag) => {
    localStorage.setItem('playerSpeed', e.currentTarget.playbackRate.toString());
  }, []);

  const handleLoadStart = useCallback(
    (e: VideoTag | AudioTag) => {
      e.currentTarget.volume = volumeFromStorage;
      e.currentTarget.playbackRate = Number(playBackSpeedFromStorage ?? 1);
    },
    [volumeFromStorage, playBackSpeedFromStorage],
  );

  const handlePause = useCallback(
    async (e: VideoTag | AudioTag) => {
      const currentTime = Number(e.currentTarget.currentTime);

      if (currentTime < 10 || currentTime > duration * 0.95) return;

      await updateVideoProgressById({
        youtubeId: videoId,
        currentProgress: currentTime,
      });
    },
    [videoId, duration],
  );

  const handleMediaEndCalled = useCallback(
    async (e: VideoTag | AudioTag) => {
      const currentTime = Number(e.currentTarget.currentTime);

      const videoProgressResponse = await updateVideoProgressById({
        youtubeId: videoId,
        currentProgress: currentTime,
      });

      const { data: videoProgressResponseData } = videoProgressResponse;

      if (videoProgressResponseData?.watched && watched !== videoProgressResponseData.watched) {
        onWatchStateChanged?.(true);
      }

      setSkippedSegments((segments: SponsorSegmentsSkippedType) => {
        const keys = Object.keys(segments);

        keys.forEach(uuid => {
          segments[uuid] = { from: 0, to: 0 };
        });

        return segments;
      });

      onVideoEnd?.();
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [videoId, watched],
  );

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLVideoElement | HTMLAudioElement>) => {
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
      e.preventDefault();
    }
  }, []);

  return (
    <>
      <div
        id="player"
        className={embed ? '' : `player-wrapper ${isTheaterMode ? 'theater-mode' : ''}`}
      >
        <div className={embed ? '' : `video-main ${isTheaterMode ? 'theater-mode' : ''}`}>
          {!audioMode && (
            <div className="video-audio-toggle-wrap">
              <video
                ref={videoRef}
                key={`${getApiUrl()}${videoUrl}`}
                poster={`${getApiUrl()}${videoThumbUrl}`}
                onVolumeChange={handleVolumeChange}
                onRateChange={handleRateChange}
                onLoadStart={handleLoadStart}
                onTimeUpdate={handleTimeUpdate(
                  videoId,
                  watched,
                  sponsorBlock,
                  setSkippedSegments,
                  onWatchStateChanged,
                )}
                onPause={handlePause}
                onEnded={handleMediaEndCalled}
                onKeyDown={handleKeyDown}
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
              <button
                className="audio-mode-icon-btn"
                onClick={() => toggleAudioMode(true)}
                title="Switch to audio only"
              >
                <img src="/img/icon-audio.svg" alt="Audio only" />
              </button>
            </div>
          )}

          {audioMode && (
            <div className="audio-card">
              <div
                className="audio-card-thumb-wrap"
                onClick={() => {
                  const audio = audioRef.current;
                  if (!audio) return;

                  if (audio.paused) {
                    audio.play();
                  } else {
                    audio.pause();
                  }
                }}
              >
                <img
                  className="audio-card-thumb"
                  src={`${getApiUrl()}${videoThumbUrl}`}
                  alt={video.title}
                />
                <button
                  className="audio-mode-icon-btn"
                  onClick={e => {
                    e.stopPropagation();
                    toggleAudioMode(false);
                  }}
                  title="Switch to video"
                >
                  <img src="/img/icon-play.svg" alt="Switch to video" />
                </button>
              </div>
              <div className="audio-card-controls">
                <audio
                  ref={audioRef}
                  onVolumeChange={handleVolumeChange}
                  onRateChange={handleRateChange}
                  onLoadStart={handleLoadStart}
                  onTimeUpdate={handleTimeUpdate(
                    videoId,
                    watched,
                    sponsorBlock,
                    setSkippedSegments,
                    onWatchStateChanged,
                  )}
                  onPause={handlePause}
                  onEnded={handleMediaEndCalled}
                  onKeyDown={handleKeyDown}
                  autoPlay={autoplay}
                  controls
                  src={`${getApiUrl()}/api/video/${videoId}/stream-mp3/`}
                  muted={isMuted}
                />
              </div>
            </div>
          )}
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
                <td>Toggle pause play</td>
                <td>p</td>
              </tr>
              <tr>
                <td>Toggle mute</td>
                <td>m</td>
              </tr>
              <tr>
                <td>Toggle fullscreen</td>
                <td>f</td>
              </tr>
              {!embed && (
                <>
                  <tr>
                    <td>Toggle theater mode</td>
                    <td>t</td>
                  </tr>
                  <tr>
                    <td>Exit theater mode</td>
                    <td>Esc</td>
                  </tr>
                </>
              )}
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
                  <a
                    href={`https://www.youtube.com/watch?v=${videoId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    this video on YouTube
                  </a>
                </u>{' '}
                and add a segment using the{' '}
                <u>
                  <a href="https://sponsor.ajay.app/" target="_blank" rel="noopener noreferrer">
                    SponsorBlock
                  </a>
                </u>{' '}
                extension.
              </h4>
            )}
            {sponsorBlock.has_unlocked && (
              <h4>
                This video has unlocked sponsor segments. Go to{' '}
                <u>
                  <a
                    href={`https://www.youtube.com/watch?v=${videoId}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    this video on YouTube
                  </a>
                </u>{' '}
                and vote on the segments using the{' '}
                <u>
                  <a href="https://sponsor.ajay.app/" target="_blank" rel="noopener noreferrer">
                    SponsorBlock
                  </a>
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
