import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteChannel = async (channelId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/channel/${channelId}/`, {
    method: 'DELETE',
    headers: defaultHeaders,
    credentials: getFetchCredentials(),

  });

  const channelDeleted = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteChannel', channelDeleted);
  }

  return channelDeleted;
};

export default deleteChannel;
