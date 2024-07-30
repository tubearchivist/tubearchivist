import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const createCustomPlaylist = async (playlistId: string) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/playlist/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },

    body: JSON.stringify({ data: { create: playlistId } }),
  });

  const customPlaylist = await response.json();
  if (isDevEnvironment()) {
    console.log('createCustomPlaylist', customPlaylist);
  }

  return customPlaylist;
};

export default createCustomPlaylist;
