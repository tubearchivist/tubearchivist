import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';

const updatePlaylistSubscription = async (playlistIds: string, status: boolean) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const playlists = [];
  const containsMultiple = playlistIds.includes('\n');

  if (containsMultiple) {
    const youtubePlaylistIds = playlistIds.split('\n');

    youtubePlaylistIds.forEach(playlistId => {
      playlists.push({ playlist_id: playlistId, playlist_subscribed: status });
    });
  } else {
    playlists.push({ playlist_id: playlistIds, playlist_subscribed: status });
  }

  const response = await fetch(`${apiUrl}/api/playlist/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),

    body: JSON.stringify({
      data: [...playlists],
    }),
  });

  const playlistSubscription = await response.json();
  console.log('updatePlaylistSubscription', playlistSubscription);

  return playlistSubscription;
};

export default updatePlaylistSubscription;
