import updateVideoProgressById from '../api/actions/updateVideoProgressById';
import updateWatchedState from '../api/actions/updateWatchedState';
import { SponsorBlockSegmentType, SponsorBlockType, VideoResponseType } from '../pages/Video';
import watchedThreshold from '../functions/watchedThreshold';
import Notifications from './Notifications';
import { Dispatch, Fragment, SetStateAction, SyntheticEvent, useState } from 'react';
import formatTime from '../functions/formatTime';
import { useSearchParams } from 'react-router-dom';
import getApiUrl from '../configuration/getApiUrl';

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

    if (currentTime < 10) return;
    if (Number((currentTime % 10).toFixed(1)) <= 0.2) {
      // Check progress every 10 seconds or else progress is checked a few times a second
      await updateVideoProgressById({
        youtubeId,
        currentProgress: currentTime,
      });

      if (!watched) {
        // Check if video is already marked as watched
        if (watchedThreshold(currentTime, duration)) {
          await updateWatchedState({
            id: youtubeId,
            is_watched: true,
          });
        }
      }
    }
  };

type VideoPlayerProps = {
  video: VideoResponseType;
  sponsorBlock?: SponsorBlockType;
  embed?: boolean;
  autoplay?: boolean;
  onVideoEnd?: () => void;
};

const VideoPlayer = ({
  video,
  sponsorBlock,
  embed,
  autoplay = false,
  onVideoEnd,
}: VideoPlayerProps) => {
  const [searchParams] = useSearchParams();
  const searchParamVideoProgress = searchParams.get('t');

  const [skippedSegments, setSkippedSegments] = useState<SponsorSegmentsSkippedType>({});

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

  const handleVideoEnd =
    (
      youtubeId: string,
      watched: boolean,
      setSponsorSegmentSkipped?: Dispatch<SetStateAction<SponsorSegmentsSkippedType>>,
    ) =>
    async () => {
      if (!watched) {
        // Check if video is already marked as watched
        await updateWatchedState({ id: youtubeId, is_watched: true });
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

  return (
    <>
      <div id="player" className={embed ? '' : 'player-wrapper'}>
        <div className={embed ? '' : 'video-main'}>
          <video
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
            )}
            onPause={async (videoTag: VideoTag) => {
              const currentTime = Number(videoTag.currentTarget.currentTime);

              if (currentTime < 10) return;

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

      <Notifications pageName="all" />
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
