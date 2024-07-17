import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadPlaylistVideosById = async (playlistId: string | undefined, page: number) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/playlist/${playlistId}/video/?page=${page}`, {
    headers,
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadPlaylistVideosById', videos);
  }

  return videos;
};

export default loadPlaylistVideosById;
