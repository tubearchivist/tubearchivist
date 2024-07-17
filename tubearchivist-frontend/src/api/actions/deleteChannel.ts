import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteChannel = async (channelId: string) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/channel/${channelId}/`, {
    method: 'DELETE',
    headers,
  });

  const channelDeleted = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteChannel', channelDeleted);
  }

  return channelDeleted;
};

export default deleteChannel;
