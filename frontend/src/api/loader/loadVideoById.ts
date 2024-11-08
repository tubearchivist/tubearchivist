import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';
import { VideoResponseType } from '../../pages/Video';

const loadVideoById = async (youtubeId: string): Promise<VideoResponseType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const videos = await response.json();

  if (isDevEnvironment()) {
    console.log('loadVideoById', videos);
  }

  return videos;
};

export default loadVideoById;
