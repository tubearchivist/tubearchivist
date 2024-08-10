import { useLoaderData, useOutletContext, useParams } from 'react-router-dom';
import Notifications from '../components/Notifications';
import Filterbar from '../components/Filterbar';
import PlaylistList from '../components/PlaylistList';
import { ViewLayoutType } from './Home';
import { ViewStyleNames, ViewStyles } from '../configuration/constants/ViewStyle';
import { UserConfigType } from '../api/actions/updateUserConfig';
import { useEffect, useState } from 'react';
import { OutletContextType } from './Base';
import Pagination from '../components/Pagination';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import { Helmet } from 'react-helmet';
import loadPlaylistList from '../api/loader/loadPlaylistList';
import { PlaylistsResponseType } from './Playlists';

type ChannelPlaylistLoaderDataType = {
  userConfig: UserConfigType;
};

const ChannelPlaylist = () => {
  const { channelId } = useParams();
  const { userConfig } = useLoaderData() as ChannelPlaylistLoaderDataType;
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const [hideWatched, setHideWatched] = useState(userConfig.hide_watched || false);
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
      const playlists = await loadPlaylistList({ channel: channelId });

      setPlaylistsResponse(playlists);
      setRefreshPlaylists(false);
    })();
  }, [channelId, refreshPlaylists, currentPage]);

  return (
    <>
      <Helmet>
        <title>TA | Channel: Playlists</title>
      </Helmet>
      <ScrollToTopOnNavigate />
      <div className={`boxed-content ${gridView}`}>
        <Notifications pageName="channel" includeReindex={true} />
        <Filterbar
          hideToggleText="Show subscribed only:"
          hideWatched={hideWatched}
          isGridView={isGridView}
          view={view}
          gridItems={gridItems}
          userConfig={userConfig}
          setHideWatched={setHideWatched}
          setView={setView}
          setGridItems={setGridItems}
          viewStyleName={ViewStyleNames.playlist}
          setRefresh={setRefreshPlaylists}
        />
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
