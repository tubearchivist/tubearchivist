import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadChannelList = async (page: number, showSubscribed: boolean) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const searchParams = new URLSearchParams();

  if (page) {
    searchParams.append('page', page.toString());
  }

  if (showSubscribed) {
    searchParams.append('filter', 'subscribed');
  }

  const response = await fetch(`${apiUrl}/api/channel/?${searchParams.toString()}`, {
    headers,
  });

  const channels = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelList', channels);
  }

  return channels;
};

export default loadChannelList;
