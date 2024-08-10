import { useLoaderData, useOutletContext, useParams } from 'react-router-dom';
import Notifications from '../components/Notifications';
import PlaylistList from '../components/PlaylistList';
import { ViewLayoutType } from './Home';
import { ViewStyles } from '../configuration/constants/ViewStyle';
import { UserConfigType } from '../api/actions/updateUserConfig';
import { useEffect, useState } from 'react';
import { OutletContextType } from './Base';
import Pagination from '../components/Pagination';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import { Helmet } from 'react-helmet';
import loadPlaylistList from '../api/loader/loadPlaylistList';
import { PlaylistsResponseType } from './Playlists';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';

type ChannelPlaylistLoaderDataType = {
  userConfig: UserConfigType;
};

const ChannelPlaylist = () => {
  const { channelId } = useParams();
  const { userConfig } = useLoaderData() as ChannelPlaylistLoaderDataType;
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const [showSubedOnly, setShowSubedOnly] = useState(userConfig.show_subed_only || false);
  const [view, setView] = useState<ViewLayoutType>(userConfig.view_style_playlist || 'grid');
  const [gridItems, setGridItems] = useState(userConfig.grid_items || 3);
  const [refreshPlaylists, setRefreshPlaylists] = useState(false);

  const [playlistsResponse, setPlaylistsResponse] = useState<PlaylistsResponseType>();

  const playlistList = playlistsResponse?.data;
  const pagination = playlistsResponse?.paginate;

  const isGridView = view === ViewStyles.grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

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
      <Helmet>
        <title>TA | Channel: Playlists</title>
      </Helmet>
      <ScrollToTopOnNavigate />
      <div className={`boxed-content ${gridView}`}>
        <Notifications pageName="channel" includeReindex={true} />

        <div className="view-controls">
          <div className="toggle">
            <span>Show subscribed only:</span>
            <div className="toggleBox">
              <input
                checked={showSubedOnly}
                onChange={() => {
                  setShowSubedOnly(!showSubedOnly);
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
                setView('grid');
              }}
              alt="grid view"
            />
            <img
              src={iconListView}
              onClick={() => {
                setView('list');
              }}
              alt="list view"
            />
          </div>
        </div>
      </div>

      <div className={`boxed-content ${gridView}`}>
        <div className={`playlist-list ${view} ${gridViewGrid}`}>
          <PlaylistList
            playlistList={playlistList}
            viewLayout={view}
            setRefresh={setRefreshPlaylists}
          />
        </div>
      </div>

      <div className="boxed-content">
        {pagination && <Pagination pagination={pagination} setPage={setCurrentPage} />}
      </div>
    </>
  );
};

export default ChannelPlaylist;
