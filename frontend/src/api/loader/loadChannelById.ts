import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadChannelById = async (youtubeChannelId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/channel/${youtubeChannelId}/`, {
    headers: defaultHeaders,
  });

  const channel = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelById', channel);
  }

  return channel;
};

export default loadChannelById;
