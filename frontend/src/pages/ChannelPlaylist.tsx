import { useOutletContext, useParams } from 'react-router-dom';
import PlaylistList from '../components/PlaylistList';
import { useEffect, useState } from 'react';
import { OutletContextType } from './Base';
import Pagination from '../components/Pagination';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import loadPlaylistList, { PlaylistsResponseType } from '../api/loader/loadPlaylistList';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import iconFilter from '/img/icon-filter.svg';
import { useUserConfigStore } from '../stores/UserConfigStore';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import { ApiResponseType } from '../functions/APIClient';
import { ViewStylesType, ViewStylesEnum } from '../configuration/constants/ViewStyle';

const ChannelPlaylist = () => {
  const { channelId } = useParams();
  const { userConfig, setUserConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const [refreshPlaylists, setRefreshPlaylists] = useState(false);
  const [showFilterItems, setShowFilterItems] = useState(false);

  const [playlistsResponse, setPlaylistsResponse] =
    useState<ApiResponseType<PlaylistsResponseType>>();

  const { data: playlistsResponseData } = playlistsResponse ?? {};

  const playlistList = playlistsResponseData?.data;
  const pagination = playlistsResponseData?.paginate;

  const viewStyle = userConfig.view_style_playlist;
  const showSubedOnly = userConfig.show_subed_only_playlists;

  const handleUserConfigUpdate = async (config: Partial<UserConfigType>) => {
    const updatedUserConfig = await updateUserConfig(config);
    const { data: updatedUserConfigData } = updatedUserConfig;

    if (updatedUserConfigData) {
      setUserConfig(updatedUserConfigData);
    }
  };

  useEffect(() => {
    (async () => {
      const playlists = await loadPlaylistList({
        channel: channelId,
        subscribed: showSubedOnly,
        page: currentPage,
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
        <div className="view-controls">
          <div className="view-icons">
            {showFilterItems && (
              <div>
                <span>Filter:</span>
                <select
                  value={
                    userConfig.show_subed_only_playlists === null
                      ? ''
                      : userConfig.show_subed_only_playlists.toString()
                  }
                  onChange={event => {
                    handleUserConfigUpdate({
                      show_subed_only_playlists:
                        event.target.value === '' ? null : event.target.value === 'true',
                    });
                    setRefreshPlaylists(true);
                  }}
                >
                  <option value="">All subscribe state</option>
                  <option value="true">Subscribed only</option>
                  <option value="false">Unsubscribed only</option>
                </select>
              </div>
            )}
            <img
              src={iconFilter}
              alt="icon filter"
              onClick={() => setShowFilterItems(!showFilterItems)}
            />
            <img
              src={iconGridView}
              onClick={() => {
                handleUserConfigUpdate({
                  view_style_playlist: ViewStylesEnum.Grid as ViewStylesType,
                });
              }}
              alt="grid view"
            />
            <img
              src={iconListView}
              onClick={() => {
                handleUserConfigUpdate({
                  view_style_playlist: ViewStylesEnum.List as ViewStylesType,
                });
              }}
              alt="list view"
            />
          </div>
        </div>
      </div>

      <div className={`boxed-content`}>
        <div className={`playlist-list ${viewStyle}`}>
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
