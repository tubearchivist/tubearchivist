import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadPlaylistVideosById = async (playlistId: string | undefined, page: number) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/playlist/${playlistId}/video/?page=${page}`, {
    headers: defaultHeaders,
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadPlaylistVideosById', videos);
  }

  return videos;
};

export default loadPlaylistVideosById;
