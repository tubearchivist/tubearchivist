import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadVideoById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/`, {
    headers: defaultHeaders,
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadVideoById', videos);
  }

  return videos;
};

export default loadVideoById;
