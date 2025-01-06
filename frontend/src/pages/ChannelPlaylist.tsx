import { useOutletContext, useParams } from 'react-router-dom';
import Notifications from '../components/Notifications';
import PlaylistList from '../components/PlaylistList';
import { useEffect, useState } from 'react';
import { OutletContextType } from './Base';
import Pagination from '../components/Pagination';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import loadPlaylistList from '../api/loader/loadPlaylistList';
import { PlaylistsResponseType } from './Playlists';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import { useUserConfigStore } from '../stores/UserConfigStore';

const ChannelPlaylist = () => {
  const { channelId } = useParams();
  const { userConfig, setPartialConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const [refreshPlaylists, setRefreshPlaylists] = useState(false);

  const [playlistsResponse, setPlaylistsResponse] = useState<PlaylistsResponseType>();

  const playlistList = playlistsResponse?.data;
  const pagination = playlistsResponse?.paginate;

  const view = userConfig.config.view_style_playlist;
  const showSubedOnly = userConfig.config.show_subed_only;

  useEffect(() => {
    (async () => {
      const playlists = await loadPlaylistList({
        channel: channelId,
        subscribed: showSubedOnly,
      });

      setPlaylistsResponse(playlists);
      setRefreshPlaylists(false);
    })();
  }, [channelId, refreshPlaylists, showSubedOnly, currentPage]);

  return (
    <>
      <title>TA | Channel: Playlists</title>
      <ScrollToTopOnNavigate />
      <div className="boxed-content">
        <Notifications pageName="channel" includeReindex={true} />

        <div className="view-controls">
          <div className="toggle">
            <span>Show subscribed only:</span>
            <div className="toggleBox">
              <input
                checked={showSubedOnly}
                onChange={() => {
                  setPartialConfig({ show_subed_only: !showSubedOnly });
                  setRefreshPlaylists(true);
                }}
                type="checkbox"
              />
              {!showSubedOnly && (
                <label htmlFor="" className="ofbtn">
                  Off
                </label>
              )}
              {showSubedOnly && (
                <label htmlFor="" className="onbtn">
                  On
                </label>
              )}
            </div>
          </div>
          <div className="view-icons">
            <img
              src={iconGridView}
              onClick={() => {
                setPartialConfig({ view_style_playlist: 'grid' });
              }}
              alt="grid view"
            />
            <img
              src={iconListView}
              onClick={() => {
                setPartialConfig({ view_style_playlist: 'list' });
              }}
              alt="list view"
            />
          </div>
        </div>
      </div>

      <div className={`boxed-content`}>
        <div className={`playlist-list ${view}`}>
          <PlaylistList playlistList={playlistList} setRefresh={setRefreshPlaylists} />
        </div>
      </div>

      <div className="boxed-content">
        {pagination && <Pagination pagination={pagination} setPage={setCurrentPage} />}
      </div>
    </>
  );
};

export default ChannelPlaylist;
