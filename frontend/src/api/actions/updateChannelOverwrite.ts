import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from "../../configuration/getApiUrl"
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from "../../functions/getCookie";

const updateChannelOverwrites = async (channelId: string, configKey: string, configValue: any) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const data = {
    channel_overwrites: {
      [configKey]: configValue
    }
  };

  const response = await fetch(`${apiUrl}/api/channel/${channelId}/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),

    body: JSON.stringify(data),
  });

  const channelSubscription = await response.json();
  console.log('updateChannelOverwrites', channelSubscription);
 
  return channelSubscription;
}

export default updateChannelOverwrites;
