import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadPlaylistVideosById = async (playlistId: string | undefined, page: number) => {
  const apiUrl = getApiUrl();
  const searchParams = new URLSearchParams();

  if (page) {
    searchParams.append('page', page.toString());
  }

  if (playlistId) {
    searchParams.append('playlist', playlistId);
  }

  const response = await fetch(`${apiUrl}/api/video/?${searchParams.toString()}`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadPlaylistVideosById', videos);
  }

  return videos;
};

export default loadPlaylistVideosById;
