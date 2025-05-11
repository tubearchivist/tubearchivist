import { useOutletContext, useParams } from 'react-router-dom';
import Notifications from '../components/Notifications';
import PlaylistList from '../components/PlaylistList';
import { useEffect, useState } from 'react';
import { OutletContextType } from './Base';
import Pagination from '../components/Pagination';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import loadPlaylistList, { PlaylistsResponseType } from '../api/loader/loadPlaylistList';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';
import { useUserConfigStore } from '../stores/UserConfigStore';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import { ApiResponseType } from '../functions/APIClient';
import { ViewStylesType, ViewStylesEnum } from '../configuration/constants/ViewStyle';

const ChannelPlaylist = () => {
  const { channelId } = useParams();
  const { userConfig, setUserConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const [refreshPlaylists, setRefreshPlaylists] = useState(false);

  const [playlistsResponse, setPlaylistsResponse] =
    useState<ApiResponseType<PlaylistsResponseType>>();

  const { data: playlistsResponseData } = playlistsResponse ?? {};

  const playlistList = playlistsResponseData?.data;
  const pagination = playlistsResponseData?.paginate;

  const view = userConfig.view_style_playlist;
  const showSubedOnly = userConfig.show_subed_only;

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
        <Notifications pageName="channel" includeReindex={true} />

        <div className="view-controls">
          <div className="toggle">
            <span>Show subscribed only:</span>
            <div className="toggleBox">
              <input
                checked={showSubedOnly}
                onChange={() => {
                  handleUserConfigUpdate({ show_subed_only: !showSubedOnly });
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
