import { Link } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { ViewLayoutType } from '../pages/Home';
import { PlaylistType } from '../pages/Playlist';
import updatePlaylistSubscription from '../api/actions/updatePlaylistSubscription';
import formatDate from '../functions/formatDates';
import Button from './Button';
import getApiUrl from '../configuration/getApiUrl';

type PlaylistListProps = {
  playlistList: PlaylistType[] | undefined;
  viewLayout: ViewLayoutType;
  setRefresh: (status: boolean) => void;
};

const PlaylistList = ({ playlistList, viewLayout, setRefresh }: PlaylistListProps) => {
  if (!playlistList || playlistList.length === 0) {
    return <p>No playlists found.</p>;
  }

  return (
    <>
      {playlistList.map((playlist: PlaylistType) => {
        return (
          <div key={playlist.playlist_id} className={`playlist-item ${viewLayout}`}>
            <div className="playlist-thumbnail">
              <Link to={Routes.Playlist(playlist.playlist_id)}>
                <img
                  src={`${getApiUrl()}/cache/playlists/${playlist.playlist_id}.jpg`}
                  alt={`${playlist.playlist_id}-thumbnail`}
                />
              </Link>
            </div>
            <div className={`playlist-desc ${viewLayout}`}>
              {playlist.playlist_type != 'custom' && (
                <Link to={Routes.Channel(playlist.playlist_channel_id)}>
                  <h3>{playlist.playlist_channel}</h3>
                </Link>
              )}

              <Link to={Routes.Playlist(playlist.playlist_id)}>
                <h2>{playlist.playlist_name}</h2>
              </Link>

              <p>Last refreshed: {formatDate(playlist.playlist_last_refresh)}</p>

              {playlist.playlist_type != 'custom' && (
                <>
                  {playlist.playlist_subscribed && (
                    <Button
                      label="Unsubscribe"
                      className="unsubscribe"
                      type="button"
                      title={`Unsubscribe from ${playlist.playlist_name}`}
                      onClick={async () => {
                        await updatePlaylistSubscription(playlist.playlist_id, false);

                        setRefresh(true);
                      }}
                    />
                  )}

                  {!playlist.playlist_subscribed && (
                    <Button
                      label="Subscribe"
                      type="button"
                      title={`Subscribe to ${playlist.playlist_name}`}
                      onClick={async () => {
                        await updatePlaylistSubscription(playlist.playlist_id, true);

                        setRefresh(true);
                      }}
                    />
                  )}
                </>
              )}
            </div>
          </div>
        );
      })}
    </>
  );
};

export default PlaylistList;
