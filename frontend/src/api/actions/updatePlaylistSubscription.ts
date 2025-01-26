import APIClient from '../../functions/APIClient';

const updatePlaylistSubscription = async (playlistId: string, status: boolean) => {
  return APIClient(`/api/playlist/${playlistId}/`, {
    method: 'POST',
    body: { playlist_subscribed: status },
  });
};

export default updatePlaylistSubscription;
