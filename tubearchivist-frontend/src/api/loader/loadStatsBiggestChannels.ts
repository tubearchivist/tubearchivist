import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

type BiggestChannelsOrderType = 'doc_count' | 'duration' | 'media_size';

const loadStatsBiggestChannels = async (order: BiggestChannelsOrderType) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const searchParams = new URLSearchParams();
  searchParams.append('order', order);

  const response = await fetch(`${apiUrl}/api/stats/biggestchannels/?${searchParams.toString()}`, {
    headers,
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadStatsBiggestChannels', notifications);
  }

  return notifications;
};

export default loadStatsBiggestChannels;
