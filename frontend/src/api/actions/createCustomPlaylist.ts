import APIClient from '../../functions/APIClient';

const createCustomPlaylist = async (playlistId: string) => {
  return APIClient('/api/playlist/custom/', {
    method: 'POST',
    body: { playlist_name: playlistId.trim() },
  });
};

export default createCustomPlaylist;
