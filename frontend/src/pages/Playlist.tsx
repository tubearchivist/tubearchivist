import { useEffect, useState } from 'react';
import { Link, useNavigate, useOutletContext, useParams, useSearchParams } from 'react-router-dom';
import loadPlaylistById, { PlaylistResponseType } from '../api/loader/loadPlaylistById';
import { OutletContextType } from './Base';
import { VideoType } from './Home';
import Filterbar from '../components/Filterbar';
import loadChannelById, { ChannelResponseType } from '../api/loader/loadChannelById';
import VideoList from '../components/VideoList';
import Pagination, { PaginationType } from '../components/Pagination';
import ChannelOverview from '../components/ChannelOverview';
import Linkify from '../components/Linkify';
import { ViewStyleNames, ViewStylesEnum } from '../configuration/constants/ViewStyle';
import updatePlaylistSubscription from '../api/actions/updatePlaylistSubscription';
import deletePlaylist from '../api/actions/deletePlaylist';
import Routes from '../configuration/routes/RouteList';
import formatDate from '../functions/formatDates';
import queueReindex from '../api/actions/queueReindex';
import updateWatchedState from '../api/actions/updateWatchedState';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import EmbeddableVideoPlayer from '../components/EmbeddableVideoPlayer';
import Button from '../components/Button';
import loadVideoListByFilter from '../api/loader/loadVideoListByPage';
import useIsAdmin from '../functions/useIsAdmin';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { ApiResponseType } from '../functions/APIClient';
import NotFound from './NotFound';

export type VideoResponseType = {
  data?: VideoType[];
  paginate?: PaginationType;
};

const Playlist = () => {
  const { playlistId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const videoId = searchParams.get('videoId');

  const { userConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;
  const isAdmin = useIsAdmin();

  const [descriptionExpanded, setDescriptionExpanded] = useState(false);
  const [refresh, setRefresh] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [reindex, setReindex] = useState(false);

  const [playlistResponse, setPlaylistResponse] = useState<ApiResponseType<PlaylistResponseType>>();
  const [channelResponse, setChannelResponse] = useState<ApiResponseType<ChannelResponseType>>();
  const [videoResponse, setVideoResponse] = useState<ApiResponseType<VideoResponseType>>();

  const { data: playlistResponseData, error: playlistResponseError } = playlistResponse ?? {};
  const { data: channelResponseData } = channelResponse ?? {};
  const { data: videoResponseData } = videoResponse ?? {};

  const playlist = playlistResponseData;
  const channel = channelResponseData;
  const videos = videoResponseData?.data;
  const pagination = videoResponseData?.paginate;

  const palylistEntries = playlistResponseData?.playlist_entries;
  const videoArchivedCount = Number(palylistEntries?.filter(video => video.downloaded).length);
  const videoInPlaylistCount = Number(palylistEntries?.length);

  const view = userConfig.view_style_home;
  const gridItems = userConfig.grid_items;
  const hideWatched = userConfig.hide_watched;
  const isGridView = view === ViewStylesEnum.Grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

  useEffect(() => {
    (async () => {
      const playlist = await loadPlaylistById(playlistId);
      const video = await loadVideoListByFilter({
        playlist: playlistId,
        page: currentPage,
        watch: hideWatched ? 'unwatched' : undefined,
      });

      setPlaylistResponse(playlist);
      setVideoResponse(video);

      const { data: playlistResponseData } = playlist ?? {};

      const isCustomPlaylist = playlistResponseData?.playlist_type === 'custom';
      if (!isCustomPlaylist) {
        const channel = await loadChannelById(playlistResponseData?.playlist_channel_id || '');
        setChannelResponse(channel);
      }
      setRefresh(false);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    playlistId,
    userConfig.hide_watched,
    refresh,
    currentPage,
    pagination?.current_page,
    videoId,
  ]);

  const errorMessage = playlistResponseError?.error;

  if (errorMessage) {
    return <NotFound failType="playlist" />;
  }

  if (!playlist || !playlistId) return [];

  const isCustomPlaylist = playlist.playlist_type === 'custom';

  return (
    <>
      <title>{`TA | Playlist: ${playlist.playlist_name}`}</title>
      <ScrollToTopOnNavigate />
      <div className="boxed-content">
        <div className="title-bar">
          <h1>{playlist.playlist_name}</h1>
        </div>
        <div className="info-box info-box-3">
          {!isCustomPlaylist && channel && (
            <ChannelOverview
              channelId={channel?.channel_id}
              channelname={channel?.channel_name}
              channelSubs={channel?.channel_subs}
              channelSubscribed={channel?.channel_subscribed}
              channelThumbUrl={channel.channel_thumb_url}
              setRefresh={setRefresh}
            />
          )}

          <div className="info-box-item">
            <div>
              <p>Last refreshed: {formatDate(playlist.playlist_last_refresh)}</p>
              {!isCustomPlaylist && (
                <>
                  <p>
                    Playlist:
                    {playlist.playlist_subscribed && (
                      <>
                        {isAdmin && (
                          <Button
                            label="Unsubscribe"
                            className="unsubscribe"
                            type="button"
                            title={`Unsubscribe from ${playlist.playlist_name}`}
                            onClick={async () => {
                              await updatePlaylistSubscription(playlistId, false);

                              setRefresh(true);
                            }}
                          />
                        )}
                      </>
                    )}{' '}
                    {!playlist.playlist_subscribed && (
                      <Button
                        label="Subscribe"
                        type="button"
                        title={`Subscribe to ${playlist.playlist_name}`}
                        onClick={async () => {
                          await updatePlaylistSubscription(playlistId, true);

                          setRefresh(true);
                        }}
                      />
                    )}
                  </p>
                  {playlist.playlist_active && (
                    <p>
                      Youtube:{' '}
                      <a
                        href={`https://www.youtube.com/playlist?list=${playlist.playlist_id}`}
                        target="_blank"
                      >
                        Active
                      </a>
                    </p>
                  )}
                  {!playlist.playlist_active && <p>Youtube: Deactivated</p>}
                </>
              )}

              {!showDeleteConfirm && (
                <Button
                  label="Delete Playlist"
                  id="delete-item"
                  onClick={() => setShowDeleteConfirm(!showDeleteConfirm)}
                />
              )}

              {showDeleteConfirm && (
                <div className="delete-confirm">
                  <span>Delete {playlist.playlist_name}?</span>

                  <Button
                    label="Delete metadata"
                    onClick={async () => {
                      await deletePlaylist(playlistId, false);
                      navigate(Routes.Playlists);
                    }}
                  />

                  <Button
                    label="Delete all"
                    className="danger-button"
                    onClick={async () => {
                      await deletePlaylist(playlistId, true);
                      navigate(Routes.Playlists);
                    }}
                  />

                  <Button label="Cancel" onClick={() => setShowDeleteConfirm(!showDeleteConfirm)} />
                </div>
              )}
            </div>
          </div>
          <div className="info-box-item">
            <div>
              {videoArchivedCount > 0 && (
                <>
                  <p>
                    Total Videos archived: {videoArchivedCount}/{videoInPlaylistCount}
                  </p>
                  <div id="watched-button" className="button-box">
                    <Button
                      label="Mark as watched"
                      title={`Mark all videos from ${playlist.playlist_name} as watched`}
                      type="button"
                      onClick={async () => {
                        await updateWatchedState({
                          id: playlistId,
                          is_watched: true,
                        });

                        setRefresh(true);
                      }}
                    />{' '}
                    <Button
                      label="Mark as unwatched"
                      title={`Mark all videos from ${playlist.playlist_name} as unwatched`}
                      type="button"
                      onClick={async () => {
                        await updateWatchedState({
                          id: playlistId,
                          is_watched: false,
                        });

                        setRefresh(true);
                      }}
                    />
                  </div>
                </>
              )}

              {reindex && <p>Reindex scheduled</p>}
              {!reindex && (
                <div id="reindex-button" className="button-box">
                  {!isCustomPlaylist && (
                    <Button
                      label="Reindex"
                      title={`Reindex Playlist ${playlist.playlist_name}`}
                      onClick={async () => {
                        setReindex(true);

                        await queueReindex(playlist.playlist_id, 'playlist');
                      }}
                    />
                  )}{' '}
                  <Button
                    label="Reindex Videos"
                    title={`Reindex Videos of ${playlist.playlist_name}`}
                    onClick={async () => {
                      setReindex(true);

                      await queueReindex(playlist.playlist_id, 'playlist', true);
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {playlist.playlist_description !== 'False' && (
          <div className="description-box">
            <p
              id={descriptionExpanded ? 'text-expand-expanded' : 'text-expand'}
              className="description-text"
            >
              <Linkify>{playlist.playlist_description}</Linkify>
            </p>

            <Button
              label="Show more"
              id="text-expand-button"
              onClick={() => setDescriptionExpanded(!descriptionExpanded)}
            />
          </div>
        )}
      </div>

      <div className={`boxed-content ${gridView}`}>
        <Filterbar
          hideToggleText="Hide watched videos:"
          viewStyleName={ViewStyleNames.home}
          showSort={false}
        />
      </div>

      <EmbeddableVideoPlayer videoId={videoId} />

      <div className={`boxed-content ${gridView}`}>
        <div className={`video-list ${view} ${gridViewGrid}`}>
          {videoInPlaylistCount === 0 && (
            <>
              <h2>No videos found...</h2>
              {isCustomPlaylist && (
                <p>
                  Try going to the <a href="{% url 'home' %}">home page</a> to add videos to this
                  playlist.
                </p>
              )}

              {!isCustomPlaylist && (
                <p>
                  Try going to the <Link to={Routes.Downloads}>downloads page</Link> to start the
                  scan and download tasks.
                </p>
              )}
            </>
          )}
          {videoInPlaylistCount !== 0 && (
            <VideoList
              videoList={videos}
              viewLayout={view}
              playlistId={playlistId}
              showReorderButton={isCustomPlaylist}
              refreshVideoList={setRefresh}
            />
          )}
        </div>
      </div>

      <div className="boxed-content">
        {pagination && <Pagination pagination={pagination} setPage={setCurrentPage} />}
      </div>
    </>
  );
};

export default Playlist;
