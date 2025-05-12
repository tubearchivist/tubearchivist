import { Link, useSearchParams } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { VideoType } from '../pages/Home';
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
import { ViewStylesType } from '../configuration/constants/ViewStyle';

type VideoListItemProps = {
  video: VideoType;
  viewStyle: ViewStylesType;
  playlistId?: string;
  showReorderButton?: boolean;
  refreshVideoList: (refresh: boolean) => void;
};

const VideoListItem = ({
  video,
  viewStyle,
  playlistId,
  showReorderButton = false,
  refreshVideoList,
}: VideoListItemProps) => {
  const [, setSearchParams] = useSearchParams();

  const [showReorderMenu, setShowReorderMenu] = useState(false);

  if (!video) {
    return <p>No video found.</p>;
  }

  return (
    <div className={`video-item ${viewStyle}`}>
      <a
        onClick={() => {
          setSearchParams(params => {
            const newParams = new URLSearchParams(params);
            newParams.set('videoId', video.youtube_id);
            return newParams;
          });
        }}
      >
        <div className={`video-thumb-wrap ${viewStyle}`}>
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
      <div className={`video-desc ${viewStyle}`}>
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
