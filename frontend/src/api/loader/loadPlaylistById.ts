import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadPlaylistById = async (playlistId: string | undefined) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/playlist/${playlistId}/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadPlaylistById', videos);
  }

  return videos;
};

export default loadPlaylistById;
