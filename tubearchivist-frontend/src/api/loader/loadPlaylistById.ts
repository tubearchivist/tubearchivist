import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadPlaylistById = async (playlistId: string | undefined) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/playlist/${playlistId}/`, {
    headers,
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadPlaylistById', videos);
  }

  return videos;
};

export default loadPlaylistById;
