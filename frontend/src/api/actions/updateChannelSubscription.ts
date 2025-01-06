import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';

const updateChannelSubscription = async (channelIds: string, status: boolean) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const channels = [];
  const containsMultiple = channelIds.includes('\n');

  if (containsMultiple) {
    const youtubeChannelIds = channelIds.split('\n');

    youtubeChannelIds.forEach(channelId => {
      channels.push({ channel_id: channelId, channel_subscribed: status });
    });
  } else {
    channels.push({ channel_id: channelIds, channel_subscribed: status });
  }

  const response = await fetch(`${apiUrl}/api/channel/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),

    body: JSON.stringify({
      data: [...channels],
    }),
  });

  const channelSubscription = await response.json();
  console.log('updateChannelSubscription', channelSubscription);

  return channelSubscription;
};

export default updateChannelSubscription;
