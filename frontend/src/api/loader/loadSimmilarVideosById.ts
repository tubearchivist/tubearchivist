import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadSimmilarVideosById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/similar/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadSimmilarVideosById', videos);
  }

  return videos;
};

export default loadSimmilarVideosById;
