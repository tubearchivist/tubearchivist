import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadChannelById = async (youtubeChannelId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/channel/${youtubeChannelId}/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const channel = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelById', channel);
  }

  return channel;
};

export default loadChannelById;
