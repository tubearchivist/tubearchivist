import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deletePlaylist = async (playlistId: string, allVideos = false) => {
  const apiUrl = getApiUrl();

  let params = '';
  if (allVideos) {
    params = '?delete-videos=true';
  }

  const response = await fetch(`${apiUrl}/api/playlist/${playlistId}/${params}`, {
    method: 'DELETE',
    headers: defaultHeaders,
  });

  const playlistDeleted = await response.json();

  if (isDevEnvironment()) {
    console.log('deletePlaylist', playlistDeleted);
  }

  return playlistDeleted;
};

export default deletePlaylist;
