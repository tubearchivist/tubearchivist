import { useLoaderData, useOutletContext, useParams } from 'react-router-dom';
import Notifications from '../components/Notifications';
import Filterbar from '../components/Filterbar';
import PlaylistList from '../components/PlaylistList';
import { ViewLayout } from './Home';
import { ViewStyleNames, ViewStyles } from '../configuration/constants/ViewStyle';
import { UserConfigType } from '../api/actions/updateUserConfig';
import { useEffect, useState } from 'react';
import { OutletContextType } from './Base';
import Pagination from '../components/Pagination';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import { Helmet } from 'react-helmet';

type ChannelPlaylistLoaderDataType = {
  userConfig: UserConfigType;
};

const ChannelPlaylist = () => {
  const { channelId } = useParams();
  const { userConfig } = useLoaderData() as ChannelPlaylistLoaderDataType;
  const [currentPage, setCurrentPage] = useOutletContext() as OutletContextType;

  const [hideWatched, setHideWatched] = useState(userConfig.hide_watched || false);
  const [view, setView] = useState<ViewLayout>(userConfig.view_style_home || 'grid');
  const [gridItems, setGridItems] = useState(userConfig.grid_items || 3);
  const [refreshPlaylist, setRefreshPlaylist] = useState(false);

  const [playlistsResponse, setPlaylistsResponse] = useState();

  const playlistList = playlistsResponse?.data;
  const pagination = playlistsResponse?.paginate;

  useEffect(() => {
    (async () => {
      const playlists = {}; // await aaaaa(channelId);

      setPlaylistsResponse(playlists);
      setRefreshPlaylist(false);
    })();
  }, [channelId, refreshPlaylist, currentPage]);

  const isGridView = view === ViewStyles.grid;
  const gridView = isGridView ? `boxed-${gridItems}` : '';
  const gridViewGrid = isGridView ? `grid-${gridItems}` : '';

  return (
    <>
      <Helmet>
        <title>TA | Channel: Playlists {channel.channel_name}</title>
      </Helmet>
      <ScrollToTopOnNavigate />
      <div className="boxed-content">
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
          setRefresh={setRefreshPlaylist}
        />
        <PlaylistList
          playlistList={playlistList}
          viewLayout={view}
          setRefresh={setRefreshPlaylist}
        />
      </div>

      <div className="boxed-content">
        {pagination && <Pagination pagination={pagination} setPage={setCurrentPage} />}
      </div>
    </>
  );
};

export default ChannelPlaylist;
