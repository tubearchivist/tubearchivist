import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';

const updatePlaylistSubscription = async (playlistId: string, status: boolean) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/playlist/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),

    body: JSON.stringify({
      data: [{ playlist_id: playlistId, playlist_subscribed: status }],
    }),
  });

  const playlistSubscription = await response.json();
  console.log('updatePlaylistSubscription', playlistSubscription);

  return playlistSubscription;
};

export default updatePlaylistSubscription;
