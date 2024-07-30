import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

const updatePlaylistSubscription = async (playlistId: string, status: boolean) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/playlist/`, {
    method: 'POST',
    headers: defaultHeaders,

    body: JSON.stringify({
      data: [{ playlist_id: playlistId, playlist_subscribed: status }],
    }),
  });

  const playlistSubscription = await response.json();
  console.log('updatePlaylistSubscription', playlistSubscription);

  return playlistSubscription;
};

export default updatePlaylistSubscription;
