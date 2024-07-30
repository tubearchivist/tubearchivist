import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

type BiggestChannelsOrderType = 'doc_count' | 'duration' | 'media_size';

const loadStatsBiggestChannels = async (order: BiggestChannelsOrderType) => {
  const apiUrl = getApiUrl();

  const searchParams = new URLSearchParams();
  searchParams.append('order', order);

  const response = await fetch(`${apiUrl}/api/stats/biggestchannels/?${searchParams.toString()}`, {
    headers: defaultHeaders,
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadStatsBiggestChannels', notifications);
  }

  return notifications;
};

export default loadStatsBiggestChannels;
