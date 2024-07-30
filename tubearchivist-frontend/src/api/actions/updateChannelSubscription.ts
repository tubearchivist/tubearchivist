import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

const updateChannelSubscription = async (channelId: string, status: boolean) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/channel/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },

    body: JSON.stringify({
      data: [{ channel_id: channelId, channel_subscribed: status }],
    }),
  });

  const channelSubscription = await response.json();
  console.log('updateChannelSubscription', channelSubscription);

  return channelSubscription;
};

export default updateChannelSubscription;
