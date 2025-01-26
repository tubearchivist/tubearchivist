import APIClient from '../../functions/APIClient';

const createCustomPlaylist = async (playlistId: string) => {
  return APIClient('/api/playlist/', {
    method: 'POST',
    body: { data: { create: playlistId } },
  });
};

export default createCustomPlaylist;
