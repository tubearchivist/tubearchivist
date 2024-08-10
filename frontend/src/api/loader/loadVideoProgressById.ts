import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadVideoProgressById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/progress/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const videoProgress = await response.json();

  if (isDevEnvironment()) {
    console.log('loadVideoProgressById', videoProgress);
  }

  return videoProgress;
};

export default loadVideoProgressById;
