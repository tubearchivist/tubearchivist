import { Link, useNavigate, useParams } from 'react-router-dom';
import loadVideoById, { VideoResponseType } from '../api/loader/loadVideoById';
import { Fragment, useEffect, useState } from 'react';
import VideoPlayer from '../components/VideoPlayer';
import iconEye from '/img/icon-eye.svg';
import iconThumb from '/img/icon-thumb.svg';
import iconStarFull from '/img/icon-star-full.svg';
import iconStarEmpty from '/img/icon-star-empty.svg';
import iconStarHalf from '/img/icon-star-half.svg';
import iconClose from '/img/icon-close.svg';
import iconUnseen from '/img/icon-unseen.svg';
import iconSeen from '/img/icon-seen.svg';
import Routes from '../configuration/routes/RouteList';
import Linkify from '../components/Linkify';
import loadSimilarVideosById from '../api/loader/loadSimilarVideosById';
import VideoList from '../components/VideoList';
import updateWatchedState from '../api/actions/updateWatchedState';
import humanFileSize from '../functions/humanFileSize';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import ChannelOverview from '../components/ChannelOverview';
import deleteVideo from '../api/actions/deleteVideo';
import capitalizeFirstLetter from '../functions/capitalizeFirstLetter';
import formatDate from '../functions/formatDates';
import formatNumbers from '../functions/formatNumbers';
import queueReindex from '../api/actions/queueReindex';
import GoogleCast from '../components/GoogleCast';
import WatchedCheckBox from '../components/WatchedCheckBox';
import convertStarRating from '../functions/convertStarRating';
import loadPlaylistList, { PlaylistsResponseType } from '../api/loader/loadPlaylistList';
import PaginationDummy from '../components/PaginationDummy';
import updateCustomPlaylist from '../api/actions/updateCustomPlaylist';
import loadCommentsbyVideoId, { CommentsResponseType } from '../api/loader/loadCommentsbyVideoId';
import CommentBox from '../components/CommentBox';
import Button from '../components/Button';
import getApiUrl from '../configuration/getApiUrl';
import loadVideoNav, { VideoNavResponseType } from '../api/loader/loadVideoNav';
import useIsAdmin from '../functions/useIsAdmin';
import ToggleConfig from '../components/ToggleConfig';
import { PlaylistType } from '../api/loader/loadPlaylistById';
import { useAppSettingsStore } from '../stores/AppSettingsStore';
import updateDownloadQueueStatusById from '../api/actions/updateDownloadQueueStatusById';
import { FileSizeUnits } from '../api/actions/updateUserConfig';
import { useUserConfigStore } from '../stores/UserConfigStore';
import NotFound from './NotFound';
import { ApiResponseType } from '../functions/APIClient';
import VideoThumbnail from '../components/VideoThumbail';
import { ViewStylesEnum, ViewStylesType } from '../configuration/constants/ViewStyle';

const isInPlaylist = (videoId: string, playlist: PlaylistType) => {
  return playlist.playlist_entries.some(entry => {
    return entry.youtube_id === videoId;
  });
};

type VideoParams = {
  videoId: string;
};

type PlaylistNavPreviousItemType = {
  youtube_id: string;
  vid_thumb: string;
  idx: number;
  title: string;
};

type PlaylistNavNextItemType = {
  youtube_id: string;
  vid_thumb: string;
  idx: number;
  title: string;
};

type PlaylistNavItemType = {
  playlist_meta: {
    current_idx: string;
    playlist_id: string;
    playlist_name: string;
    playlist_channel: string;
  };
  playlist_previous: PlaylistNavPreviousItemType;
  playlist_next: PlaylistNavNextItemType;
};

export type PlaylistNavType = PlaylistNavItemType[];

export type SponsorBlockSegmentType = {
  category: string;
  actionType: string;
  segment: number[];
  UUID: string;
  videoDuration: number;
  locked: number;
  votes: number;
};

export type SponsorBlockType = {
  last_refresh: number;
  has_unlocked: boolean;
  is_enabled: boolean;
  segments: SponsorBlockSegmentType[];
  message?: string;
};

const Video = () => {
  const { videoId } = useParams() as VideoParams;
  const navigate = useNavigate();
  const isAdmin = useIsAdmin();
  const { appSettingsConfig } = useAppSettingsStore();
  const { userConfig } = useUserConfigStore();

  const [videoEnded, setVideoEnded] = useState(false);
  const [playlistAutoplay, setPlaylistAutoplay] = useState(
    localStorage.getItem('playlistAutoplay') === 'true',
  );
  const [playlistIdForAutoplay, setPlaylistIDForAutoplay] = useState<string | undefined>(
    localStorage.getItem('playlistIdForAutoplay') ?? '',
  );
  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showAddToPlaylist, setShowAddToPlaylist] = useState(false);
  const [refreshVideoList, setRefreshVideoList] = useState(false);
  const [reindex, setReindex] = useState(false);

  const [videoResponse, setVideoResponse] = useState<ApiResponseType<VideoResponseType>>();
  const [similarVideos, setSimilarVideos] = useState<ApiResponseType<VideoResponseType[]>>();
  const [videoPlaylistNav, setVideoPlaylistNav] =
    useState<ApiResponseType<VideoNavResponseType[]>>();
  const [customPlaylistsResponse, setCustomPlaylistsResponse] =
    useState<ApiResponseType<PlaylistsResponseType>>();
  const [commentsResponse, setCommentsResponse] = useState<ApiResponseType<CommentsResponseType>>();

  const { data: videoResponseData, error: videoResponseError } = videoResponse ?? {};
  const { data: similarVideosResponseData } = similarVideos ?? {};
  const { data: videoPlaylistNavResponseData } = videoPlaylistNav ?? {};
  const { data: customPlaylistsResponseData } = customPlaylistsResponse ?? {};
  const { data: commentsResponseData } = commentsResponse ?? {};

  useEffect(() => {
    (async () => {
      if (refreshVideoList || videoId !== videoResponseData?.youtube_id) {
        const videoByIdResponse = await loadVideoById(videoId);
        setVideoResponse(videoByIdResponse);

        const similarVideosResponse = await loadSimilarVideosById(videoId);
        const customPlaylistsResponse = await loadPlaylistList({ type: 'custom' });
        const videoNavResponse = await loadVideoNav(videoId);

        try {
          const commentsResponse = await loadCommentsbyVideoId(videoId);
          setCommentsResponse(commentsResponse);
        } catch (e) {
          console.log('Comments not found', e);
        }

        setSimilarVideos(similarVideosResponse);
        setVideoPlaylistNav(videoNavResponse);
        setCustomPlaylistsResponse(customPlaylistsResponse);

        setRefreshVideoList(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoId, refreshVideoList]);

  useEffect(() => {
    localStorage.setItem('playlistAutoplay', playlistAutoplay.toString());

    if (!playlistAutoplay) {
      localStorage.setItem('playlistIdForAutoplay', '');

      return;
    }

    localStorage.setItem('playlistIdForAutoplay', playlistIdForAutoplay || '');
  }, [playlistAutoplay, playlistIdForAutoplay]);

  useEffect(() => {
    if (videoEnded && playlistAutoplay) {
      const playlist = videoPlaylistNavResponseData?.find(playlist => {
        return playlist.playlist_meta.playlist_id === playlistIdForAutoplay;
      });

      if (playlist) {
        const nextYoutubeId = playlist.playlist_next?.youtube_id;

        if (nextYoutubeId) {
          setVideoEnded(false);
          navigate(Routes.Video(nextYoutubeId));
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [videoEnded, playlistAutoplay]);

  const errorMessage = videoResponseError?.error;

  if (errorMessage) {
    return <NotFound failType="video" />;
  }

  if (videoResponseData === undefined) {
    return [];
  }

  const video = videoResponseData;
  const watched = video.player.watched;
  const playlistNav = videoPlaylistNavResponseData;
  const sponsorBlock = video.sponsorblock;
  const customPlaylists = customPlaylistsResponseData?.data;
  const starRating = convertStarRating(video?.stats?.average_rating);
  const comments = commentsResponseData;
  const useSiUnits = userConfig.file_size_unit === FileSizeUnits.Metric;

  console.log('playlistNav', playlistNav);

  const cast = appSettingsConfig.application.enable_cast;

  return (
    <>
      <title>{`TA | ${video.title}`}</title>
      <ScrollToTopOnNavigate />

      <VideoPlayer
        video={video}
        sponsorBlock={sponsorBlock}
        autoplay={playlistAutoplay}
        onWatchStateChanged={() => {
          setRefreshVideoList(true);
        }}
        onVideoEnd={() => {
          setVideoEnded(true);
        }}
      />

      <div className="boxed-content">
        <div className="title-bar">
          {cast && (
            <GoogleCast
              video={video}
              setRefresh={() => {
                setRefreshVideoList(true);
              }}
              onWatchStateChanged={() => {
                setRefreshVideoList(true);
              }}
            />
          )}
          <h1 id="video-title">{video.title}</h1>
        </div>
        <div className="info-box info-box-3">
          <ChannelOverview
            channelId={video.channel.channel_id}
            channelname={video.channel.channel_name}
            channelSubs={video.channel.channel_subs}
            channelSubscribed={video.channel.channel_subscribed}
            channelThumbUrl={video.channel.channel_thumb_url}
            setRefresh={setRefreshVideoList}
          />

          <div className="info-box-item">
            <div>
              <p>Published: {formatDate(video.published)}</p>
              <p>Last refreshed: {formatDate(video.vid_last_refresh)}</p>
              <p className="video-info-watched">
                Watched:
                <WatchedCheckBox
                  watched={watched}
                  onClick={async status => {
                    await updateWatchedState({
                      id: videoId,
                      is_watched: status,
                    });
                  }}
                  onDone={() => {
                    setRefreshVideoList(true);
                  }}
                />
              </p>
              {video.active && (
                <p>
                  Youtube:{' '}
                  <a href={`https://www.youtube.com/watch?v=${video.youtube_id}`} target="_blank">
                    Active
                  </a>
                </p>
              )}
              {!video.active && <p>Youtube: Deactivated</p>}
            </div>
          </div>
          <div className="info-box-item">
            <div>
              <p className="thumb-icon">
                <img src={iconEye} alt="views" />: {formatNumbers(video.stats.view_count)}
              </p>
              <p className="thumb-icon like">
                <img src={iconThumb} alt="thumbs-up" />: {formatNumbers(video.stats.like_count)}
              </p>
              {video.stats.dislike_count > 0 && (
                <p className="thumb-icon">
                  <img className="dislike" src={iconThumb} alt="thumbs-down" />:{' '}
                  {formatNumbers(video.stats.dislike_count)}
                </p>
              )}
              {video?.stats && starRating && (
                <div className="rating-stars">
                  {starRating?.map?.((star, index) => {
                    if (star === 'full') {
                      return <img key={index} src={iconStarFull} alt={star} />;
                    }

                    if (star === 'half') {
                      return <img key={index} src={iconStarHalf} alt={star} />;
                    }

                    return <img key={index} src={iconStarEmpty} alt={star} />;
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="info-box info-box-2">
          <div className="info-box-item">
            <div className="button-box">
              {reindex && <p>Reindex scheduled</p>}
              {!reindex && (
                <>
                  {isAdmin && (
                    <div id="reindex-button">
                      <Button
                        label="Reindex"
                        title={`Reindex ${video.title}`}
                        onClick={async () => {
                          await queueReindex(video.youtube_id, 'video');
                          setReindex(true);
                        }}
                      />
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="button-box">
              <a download="" href={`${getApiUrl()}${video.media_url}`}>
                <Button label="Download File" id="download-item" />
              </a>
            </div>

            <div className="button-box">
              {isAdmin && (
                <>
                  {!showDeleteConfirm && (
                    <Button
                      label="Delete Video"
                      id="delete-item"
                      onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
                    />
                  )}

                  {showDeleteConfirm && (
                    <div className="delete-confirm">
                      <span>Are you sure? </span>

                      <Button
                        label="Delete"
                        className="danger-button"
                        onClick={async () => {
                          await deleteVideo(videoId);
                          navigate(Routes.Channel(video.channel.channel_id));
                        }}
                      />
                      <Button
                        label="Delete and Ignore"
                        className="danger-button"
                        onClick={async () => {
                          await deleteVideo(videoId);
                          await updateDownloadQueueStatusById(videoId, 'ignore-force');
                          navigate(Routes.Channel(video.channel.channel_id));
                        }}
                      />
                      <Button
                        label="Cancel"
                        onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
                      />
                    </div>
                  )}
                </>
              )}{' '}
            </div>

            <div className="button-box">
              {!showAddToPlaylist && (
                <Button
                  label="Add To Playlist"
                  id={`${video.youtube_id}-button`}
                  data-id={video.youtube_id}
                  data-context="video"
                  onClick={() => {
                    setShowAddToPlaylist(true);
                  }}
                />
              )}

              {showAddToPlaylist && (
                <>
                  <div className="video-popup-menu">
                    <img
                      src={iconClose}
                      className="video-popup-menu-close-button"
                      title="Close menu"
                      onClick={() => {
                        setShowAddToPlaylist(false);
                      }}
                    />
                    <h3>Add video to...</h3>

                    {customPlaylists?.map(playlist => {
                      return (
                        <p
                          onClick={async () => {
                            if (isInPlaylist(videoId, playlist)) {
                              await updateCustomPlaylist('remove', playlist.playlist_id, videoId);
                            } else {
                              await updateCustomPlaylist('create', playlist.playlist_id, videoId);
                            }

                            setRefreshVideoList(true);
                          }}
                        >
                          {isInPlaylist(videoId, playlist) && (
                            <img className="p-button" src={iconSeen} />
                          )}

                          {!isInPlaylist(videoId, playlist) && (
                            <img className="p-button" src={iconUnseen} />
                          )}

                          {playlist.playlist_name}
                        </p>
                      );
                    })}

                    <p>
                      <Link to={Routes.Playlists}>Create playlist</Link>
                    </p>
                  </div>
                </>
              )}
            </div>
          </div>
          <div className="info-box-item">
            {video.media_size && <p>File size: {humanFileSize(video.media_size, useSiUnits)}</p>}

            {video.streams &&
              video.streams.map(stream => {
                return (
                  <p key={stream.index}>
                    {capitalizeFirstLetter(stream.type)}: {stream.codec}{' '}
                    {humanFileSize(stream.bitrate, useSiUnits)}/s
                    {stream.width && (
                      <>
                        <span className="space-carrot">|</span> {stream.width}x{stream.height}
                      </>
                    )}{' '}
                  </p>
                );
              })}
          </div>
        </div>
        {video.tags && video.tags.length > 0 && (
          <div className="description-box">
            <div className="video-tag-box">
              {video.tags.map(tag => {
                return (
                  <span key={tag} className="video-tag">
                    {tag}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {video.description && (
          <div className="description-box">
            <p
              id={descriptionExpanded ? 'text-expand-expanded' : 'text-expand'}
              className="description-text"
            >
              <Linkify>{video.description}</Linkify>
            </p>

            <Button
              label={descriptionExpanded ? 'Show less' : 'Show more'}
              id="text-expand-button"
              onClick={() => setDescriptionExpanded(!descriptionExpanded)}
            />
          </div>
        )}

        {playlistNav && (
          <>
            {playlistNav.map(playlistItem => {
              return (
                <div key={playlistItem.playlist_meta.playlist_id} className="playlist-wrap">
                  <Link to={Routes.Playlist(playlistItem.playlist_meta.playlist_id)}>
                    <h3>
                      Playlist [{playlistItem.playlist_meta.current_idx + 1}
                      ]: {playlistItem.playlist_meta.playlist_name}
                    </h3>
                  </Link>

                  <ToggleConfig
                    name="playlist-autoplay"
                    text="Autoplay:"
                    value={
                      playlistAutoplay &&
                      playlistIdForAutoplay === playlistItem.playlist_meta.playlist_id
                    }
                    updateCallback={(_, checked) => {
                      if (checked) {
                        setPlaylistIDForAutoplay(playlistItem.playlist_meta.playlist_id);
                        setPlaylistAutoplay(true);

                        return;
                      }

                      setPlaylistIDForAutoplay('');
                      setPlaylistAutoplay(false);
                    }}
                  />

                  <div className="playlist-nav">
                    <div className="playlist-nav-item">
                      {playlistItem.playlist_previous && (
                        <>
                          <Link to={Routes.Video(playlistItem.playlist_previous.youtube_id)}>
                            <VideoThumbnail
                              videoThumbUrl={playlistItem.playlist_previous.vid_thumb}
                            />
                          </Link>
                          <div className="playlist-desc">
                            <p>Previous:</p>
                            <Link to={Routes.Video(playlistItem.playlist_previous.youtube_id)}>
                              <h3>
                                [{playlistItem.playlist_previous.idx + 1}]{' '}
                                {playlistItem.playlist_previous.title}
                              </h3>
                            </Link>
                          </div>
                        </>
                      )}
                    </div>
                    <div className="playlist-nav-item">
                      {playlistItem.playlist_next && (
                        <>
                          <div className="playlist-desc">
                            <p>Next:</p>
                            <Link to={Routes.Video(playlistItem.playlist_next.youtube_id)}>
                              <h3>
                                [{playlistItem.playlist_next.idx + 1}]{' '}
                                {playlistItem.playlist_next.title}
                              </h3>
                            </Link>
                          </div>
                          <Link to={Routes.Video(playlistItem.playlist_next.youtube_id)}>
                            <VideoThumbnail videoThumbUrl={playlistItem.playlist_next.vid_thumb} />
                          </Link>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </>
        )}

        <div className="description-box">
          <h3>Similar Videos</h3>
          <div className="video-list grid grid-3" id="similar-videos">
            <VideoList
              videoList={similarVideosResponseData}
              viewLayout={ViewStylesEnum.Grid as ViewStylesType}
              refreshVideoList={setRefreshVideoList}
            />
          </div>
        </div>

        {video.comment_count == 0 && (
          <div className="comments-section">
            <span>Video has no comments</span>
          </div>
        )}

        {video.comment_count && (
          <div className="comments-section">
            <h3>Comments: {video.comment_count}</h3>
            <div id="comments-list" className="comments-list">
              {comments?.map(comment => {
                return (
                  <Fragment key={comment.comment_id}>
                    <CommentBox comment={comment} />
                  </Fragment>
                );
              })}
            </div>
          </div>
        )}
        <div className="boxed-content-empty" />
      </div>

      <PaginationDummy />
    </>
  );
};

export default Video;
