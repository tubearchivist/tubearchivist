import APIClient from '../../functions/APIClient';

const updateBulkPlaylistSubscriptions = async (playlistIds: string, status: boolean) => {
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

  return APIClient('/api/playlist/', {
    method: 'POST',
    body: { data: [...playlists] },
  });
};

export default updateBulkPlaylistSubscriptions;
