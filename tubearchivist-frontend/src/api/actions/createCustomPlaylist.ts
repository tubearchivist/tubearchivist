import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const createCustomPlaylist = async (playlistId: string) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/playlist/`, {
    method: 'POST',
    headers,

    body: JSON.stringify({ data: { create: playlistId } }),
  });

  const customPlaylist = await response.json();
  if (isDevEnvironment()) {
    console.log('createCustomPlaylist', customPlaylist);
  }

  return customPlaylist;
};

export default createCustomPlaylist;
