import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteChannel = async (channelId: string) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/channel/${channelId}/`, {
    method: 'DELETE',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
  });

  const channelDeleted = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteChannel', channelDeleted);
  }

  return channelDeleted;
};

export default deleteChannel;
