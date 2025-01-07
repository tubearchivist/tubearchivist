import APIClient from '../../functions/APIClient';

const loadPlaylistById = async (playlistId: string | undefined) => {
  return APIClient(`/api/playlist/${playlistId}/`);
};

export default loadPlaylistById;
