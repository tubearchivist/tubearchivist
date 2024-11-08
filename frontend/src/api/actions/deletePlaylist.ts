import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deletePlaylist = async (playlistId: string, allVideos = false) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  let params = '';
  if (allVideos) {
    params = '?delete-videos=true';
  }

  const response = await fetch(`${apiUrl}/api/playlist/${playlistId}/${params}`, {
    method: 'DELETE',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
  });

  const playlistDeleted = await response.json();

  if (isDevEnvironment()) {
    console.log('deletePlaylist', playlistDeleted);
  }

  return playlistDeleted;
};

export default deletePlaylist;
