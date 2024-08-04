import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadChannelList = async (page: number, showSubscribed: boolean) => {
  const apiUrl = getApiUrl();

  const searchParams = new URLSearchParams();

  if (page) {
    searchParams.append('page', page.toString());
  }

  if (showSubscribed) {
    searchParams.append('filter', 'subscribed');
  }

  const response = await fetch(`${apiUrl}/api/channel/?${searchParams.toString()}`, {
    headers: defaultHeaders,
  });

  const channels = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelList', channels);
  }

  return channels;
};

export default loadChannelList;
