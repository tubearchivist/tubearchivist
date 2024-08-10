import { useEffect, useState } from 'react';
import { useLoaderData, useOutletContext } from 'react-router-dom';

import iconAdd from '/img/icon-add.svg';
import iconGridView from '/img/icon-gridview.svg';
import iconListView from '/img/icon-listview.svg';

import { OutletContextType } from './Base';
import updateUserConfig, { UserConfigType } from '../api/actions/updateUserConfig';
import loadPlaylistList from '../api/loader/loadPlaylistList';
import { ConfigType, ViewLayoutType } from './Home';
import Pagination, { PaginationType } from '../components/Pagination';
import PlaylistList from '../components/PlaylistList';
import { PlaylistType } from './Playlist';
import updatePlaylistSubscription from '../api/actions/updatePlaylistSubscription';
import createCustomPlaylist from '../api/actions/createCustomPlaylist';
import ScrollToTopOnNavigate from '../components/ScrollToTop';
import { Helmet } from 'react-helmet';
import Button from '../components/Button';

export type PlaylistEntryType = {
  youtube_id: string;
  title: string;
  uploader: string;
  idx: number;
  downloaded: boolean;
};

export type PlaylistsResponseType = {
  data?: PlaylistType[];
  config?: ConfigType;
  paginate?: PaginationType;
};

type PlaylistLoaderDataType = {
  userConfig: UserConfigType;
};

const Playlists = () => {
  const { userConfig } = useLoaderData() as PlaylistLoaderDataType;
  const { isAdmin, currentPage, setCurrentPage } = useOutletContext() as OutletContextType;

  const [showSubedOnly, setShowSubedOnly] = useState(userConfig.show_subed_only || false);
  const [view, setView] = useState<ViewLayoutType>(userConfig.view_style_playlist || 'grid');
  const [showAddForm, setShowAddForm] = useState(false);
  const [refresh, setRefresh] = useState(false);
  const [playlistsToAddText, setPlaylistsToAddText] = useState('');
  const [customPlaylistsToAddText, setCustomPlaylistsToAddText] = useState('');

  const [playlistResponse, setPlaylistReponse] = useState<PlaylistsResponseType>();

  const playlistList = playlistResponse?.data;
  const pagination = playlistResponse?.paginate;

  const hasPlaylists = playlistResponse?.data?.length !== 0;

  useEffect(() => {
    (async () => {
      if (userConfig.view_style_playlist !== view || userConfig.show_subed_only !== showSubedOnly) {
        const userConfig: UserConfigType = {
          show_subed_only: showSubedOnly,
          view_style_playlist: view,
        };

        await updateUserConfig(userConfig);
      }
    })();
  }, [showSubedOnly, userConfig.show_subed_only, userConfig.view_style_playlist, view]);

  useEffect(() => {
    (async () => {
      if (
        refresh ||
        pagination?.current_page === undefined ||
        currentPage !== pagination?.current_page
      ) {
        const playlist = await loadPlaylistList({ page: currentPage });

        setPlaylistReponse(playlist);
        setRefresh(false);
      }
    })();
  }, [refresh, currentPage, showSubedOnly, view, pagination?.current_page]);

  return (
    <>
      <Helmet>
        <title>TA | Playlists</title>
      </Helmet>
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
                        await updatePlaylistSubscription(playlistsToAddText, true);
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
                        await createCustomPlaylist(customPlaylistsToAddText);
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div id="notifications"></div>

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

        <div className={`playlist-list ${view}`}>
          {!hasPlaylists && <h2>No playlists found...</h2>}

          {hasPlaylists && (
            <PlaylistList playlistList={playlistList} viewLayout={view} setRefresh={setRefresh} />
          )}
        </div>
      </div>

      <div className="boxed-content">
        {pagination && <Pagination pagination={pagination} setPage={setCurrentPage} />}
      </div>
    </>
  );
};

export default Playlists;
