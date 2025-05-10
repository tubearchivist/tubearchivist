import { Link, useSearchParams } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { VideoType, ViewLayoutType } from '../pages/Home';
import iconPlay from '/img/icon-play.svg';
import iconDotMenu from '/img/icon-dot-menu.svg';
import iconClose from '/img/icon-close.svg';
import updateWatchedState from '../api/actions/updateWatchedState';
import formatDate from '../functions/formatDates';
import WatchedCheckBox from './WatchedCheckBox';
import MoveVideoMenu from './MoveVideoMenu';
import { useState } from 'react';
import deleteVideoProgressById from '../api/actions/deleteVideoProgressById';
import VideoThumbnail from './VideoThumbail';
import { FileSizeUnits } from '../api/actions/updateUserConfig';
import { useUserConfigStore } from '../stores/UserConfigStore';
import humanFileSize from '../functions/humanFileSize';

type VideoListItemProps = {
  video: VideoType;
  viewLayout: ViewLayoutType;
  playlistId?: string;
  showReorderButton?: boolean;
  refreshVideoList: (refresh: boolean) => void;
};

const VideoListItem = ({
  video,
  viewLayout,
  playlistId,
  showReorderButton = false,
  refreshVideoList,
}: VideoListItemProps) => {
  const [, setSearchParams] = useSearchParams();
  const { userConfig } = useUserConfigStore();

  const [showReorderMenu, setShowReorderMenu] = useState(false);

  if (!video) {
    return <p>No video found.</p>;
  }

  const useSiUnits = userConfig.file_size_unit === FileSizeUnits.Metric;
  const [videoStream, audioStream] = video.streams;

  return (
    <div className={`video-item ${viewLayout}`}>
      <a
        onClick={() => {
          setSearchParams(params => {
            const newParams = new URLSearchParams(params);
            newParams.set('videoId', video.youtube_id);
            return newParams;
          });
        }}
      >
        <div className={`video-thumb-wrap ${viewLayout}`}>
          <div className="video-thumb">
            <VideoThumbnail videoThumbUrl={video.vid_thumb_url} />

            {video.player.progress && (
              <div
                className="video-progress-bar"
                id={`progress-${video.youtube_id}`}
                style={{
                  width: `${video.player.progress}%`,
                }}
              ></div>
            )}
            {!video.player.progress && (
              <div
                className="video-progress-bar"
                id={`progress-${video.youtube_id}`}
                style={{ width: '0%' }}
              ></div>
            )}
          </div>
          <div className="video-play">
            <img src={iconPlay} alt="play-icon" />
          </div>
        </div>
      </a>
      <div className={`video-desc ${viewLayout}`}>
        <div className="video-desc-player" id={`video-info-${video.youtube_id}`}>
          <WatchedCheckBox
            watched={video.player.watched}
            onClick={async status => {
              await updateWatchedState({
                id: video.youtube_id,
                is_watched: status,
              });
            }}
            onDone={() => {
              refreshVideoList(true);
            }}
          />
          {video.player.progress && (
            <img
              src={iconClose}
              className="video-popup-menu-close-button"
              title="Delete watch progress"
              onClick={async () => {
                await deleteVideoProgressById(video.youtube_id);
                refreshVideoList(true);
              }}
            />
          )}
          <span>
            {formatDate(video.published)} | {video.player.duration_str}
          </span>
        </div>
        <div className="video-desc-details">
          <div>
            <Link to={Routes.Channel(video.channel.channel_id)}>
              <h3>{video.channel.channel_name}</h3>
            </Link>
            <Link className="video-more" to={Routes.Video(video.youtube_id)}>
              <h2>{video.title}</h2>
            </Link>

            {viewLayout === 'list' && (
              <>
                <p>
                  {videoStream.width}x{videoStream.height} {videoStream.codec}{' '}
                  {humanFileSize(videoStream.bitrate, useSiUnits)}
                </p>
                <p>
                  {audioStream.codec} {humanFileSize(audioStream.bitrate, useSiUnits)}
                </p>
              </>
            )}
          </div>

          {showReorderButton && !showReorderMenu && (
            <img
              src={iconDotMenu}
              alt="dot-menu-icon"
              className="dot-button"
              title="More actions"
              onClick={() => {
                setShowReorderMenu(true);
              }}
            />
          )}
        </div>

        {showReorderButton && showReorderMenu && (
          <MoveVideoMenu
            playlistId={playlistId}
            videoId={video.youtube_id}
            setCloseMenu={status => setShowReorderMenu(!status)}
            setRefresh={refreshVideoList}
          />
        )}
      </div>
    </div>
  );
};

export default VideoListItem;
