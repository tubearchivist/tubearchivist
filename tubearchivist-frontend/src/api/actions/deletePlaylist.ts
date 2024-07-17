import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deletePlaylist = async (playlistId: string, allVideos = false) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  let params = '';
  if (allVideos) {
    params = '?delete-videos=true';
  }

  const response = await fetch(`${apiUrl}/api/playlist/${playlistId}/${params}`, {
    method: 'DELETE',
    headers,
  });

  const playlistDeleted = await response.json();

  if (isDevEnvironment()) {
    console.log('deletePlaylist', playlistDeleted);
  }

  return playlistDeleted;
};

export default deletePlaylist;
