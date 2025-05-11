import { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import iconAdd from '/img/icon-add.svg';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';

import { OutletContextType } from './Base';
import loadPlaylistList, { PlaylistsResponseType } from '../api/loader/loadPlaylistList';
import Pagination from '../components/Pagination';
import PlaylistList from '../components/PlaylistList';
import updateBulkPlaylistSubscriptions from '../api/actions/updateBulkPlaylistSubscriptions';
import createCustomPlaylist from '../api/actions/createCustomPlaylist';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import Button from '../components/Button';
import useIsAdmin from '../functions/useIsAdmin';
import { useUserConfigStore } from '../stores/UserConfigStore';
import Notifications from '../components/Notifications';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import { ApiResponseType } from '../functions/APIClient';
import { ViewStylesEnum, ViewStylesType } from '../configuration/constants/ViewStyle';

const Playlists = () => {
  const { userConfig, setUserConfig } = useUserConfigStore();
  const { currentPage, setCurrentPage } = useOutletContext() as OutletContextType;
  const isAdmin = useIsAdmin();

  const [showAddForm, setShowAddForm] = useState(false);
  const [refresh, setRefresh] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [playlistsToAddText, setPlaylistsToAddText] = useState('');
  const [customPlaylistsToAddText, setCustomPlaylistsToAddText] = useState('');

  const [playlistResponse, setPlaylistReponse] = useState<ApiResponseType<PlaylistsResponseType>>();

  const { data: playlistResponseData } = playlistResponse ?? {};

  const playlistList = playlistResponseData?.data;
  const pagination = playlistResponseData?.paginate;

  const hasPlaylists = playlistResponseData?.data?.length !== 0;

  const view = userConfig.view_style_playlist;
  const showSubedOnly = userConfig.show_subed_only;

  useEffect(() => {
    (async () => {
      const playlist = await loadPlaylistList({
        page: currentPage,
        subscribed: showSubedOnly,
      });

      setPlaylistReponse(playlist);
      setRefresh(false);
      setShowNotification(false);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refresh, userConfig.show_subed_only, currentPage, pagination?.current_page]);

  const handleUserConfigUpdate = async (config: Partial<UserConfigType>) => {
    const updatedUserConfig = await updateUserConfig(config);
    const { data: updatedUserConfigData } = updatedUserConfig;

    if (updatedUserConfigData) {
      setUserConfig(updatedUserConfigData);
    }
  };

  return (
    <>
      <title>TA | Playlists</title>
      <ScrollToTopOnNavigate />
      <div className="boxed-content">
        <div className="title-split">
          <div className="title-bar">
            <h1>Playlists</h1>
          </div>
          {isAdmin && (
            <div className="title-split-form">
              <img
                onClick={() => {
                  setShowAddForm(!showAddForm);
                }}
                src={iconAdd}
                alt="add-icon"
                title="Subscribe to Playlists"
              />
              {showAddForm && (
                <div className="show-form">
                  <div>
                    <label>Subscribe to playlists:</label>
                    <textarea
                      value={playlistsToAddText}
                      onChange={event => {
                        setPlaylistsToAddText(event.target.value);
                      }}
                      rows={3}
                      cols={40}
                      placeholder="Input playlist IDs or URLs"
                    />

                    <Button
                      label="Subscribe"
                      type="submit"
                      onClick={async () => {
                        if (playlistsToAddText.trim()) {
                          await updateBulkPlaylistSubscriptions(playlistsToAddText, true);
                          setShowNotification(true);
                          setShowAddForm(false);
                        }
                      }}
                    />
                  </div>
                  <br />
                  <div>
                    <label>Or create custom playlist:</label>
                    <textarea
                      rows={1}
                      cols={40}
                      placeholder="Input playlist name"
                      value={customPlaylistsToAddText}
                      onChange={event => {
                        setCustomPlaylistsToAddText(event.target.value);
                      }}
                    />

                    <Button
                      label="Create"
                      type="submit"
                      onClick={async () => {
                        if (customPlaylistsToAddText.trim()) {
                          await createCustomPlaylist(customPlaylistsToAddText);
                          setRefresh(true);
                        }
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <Notifications
          pageName="all"
          update={showNotification}
          setShouldRefresh={isDone => {
            if (!isDone) {
              setRefresh(true);
            }
          }}
        />

        <div className="view-controls">
          <div className="toggle">
            <span>Show subscribed only:</span>
            <div className="toggleBox">
              <input
                checked={showSubedOnly}
                onChange={() => {
                  handleUserConfigUpdate({ show_subed_only: !showSubedOnly });
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

        <div className={`playlist-list ${view}`}>
          {!hasPlaylists && <h2>No playlists found...</h2>}

          {hasPlaylists && <PlaylistList playlistList={playlistList} setRefresh={setRefresh} />}
        </div>
      </div>

      <div className="boxed-content">
        {pagination && <Pagination pagination={pagination} setPage={setCurrentPage} />}
      </div>
    </>
  );
};

export default Playlists;
