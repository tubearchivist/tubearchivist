import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadPlaylistList = async (page: number | undefined, isCustom = false) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const searchParams = new URLSearchParams();

  if (page) {
    searchParams.append('page', page.toString());
  }

  if (isCustom) {
    searchParams.append('playlist_type', 'custom');
  }

  const response = await fetch(`${apiUrl}/api/playlist/?${searchParams.toString()}`, {
    headers,
  });

  const playlist = await response.json();

  if (isDevEnvironment()) {
    console.log('loadPlaylistList', playlist);
  }

  return playlist;
};

export default loadPlaylistList;
