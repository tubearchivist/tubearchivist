import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

const updatePlaylistSubscription = async (playlistId: string, status: boolean) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/playlist/`, {
    method: 'POST',
    headers,

    body: JSON.stringify({
      data: [{ playlist_id: playlistId, playlist_subscribed: status }],
    }),
  });

  const playlistSubscription = await response.json();
  console.log('updatePlaylistSubscription', playlistSubscription);

  return playlistSubscription;
};

export default updatePlaylistSubscription;
