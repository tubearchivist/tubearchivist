import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadPlaylistList = async (page: number | undefined, isCustom = false) => {
  const apiUrl = getApiUrl();

  const searchParams = new URLSearchParams();

  if (page) {
    searchParams.append('page', page.toString());
  }

  if (isCustom) {
    searchParams.append('playlist_type', 'custom');
  }

  const response = await fetch(`${apiUrl}/api/playlist/?${searchParams.toString()}`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const playlist = await response.json();

  if (isDevEnvironment()) {
    console.log('loadPlaylistList', playlist);
  }

  return playlist;
};

export default loadPlaylistList;
