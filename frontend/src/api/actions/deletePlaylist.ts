import APIClient from '../../functions/APIClient';

const deletePlaylist = async (playlistId: string, allVideos = false) => {
  let params = '';
  if (allVideos) {
    params = '?delete-videos=true';
  }

  return APIClient(`/api/playlist/${playlistId}/${params}`, {
    method: 'DELETE',
  });
};

export default deletePlaylist;
