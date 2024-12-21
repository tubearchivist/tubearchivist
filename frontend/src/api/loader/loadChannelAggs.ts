import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

export type ChannelAggsType = {
  total_items: {
    value: number;
  };
  total_size: {
    value: number;
  };
  total_duration: {
    value: number;
    value_str: string;
  };
};

const loadChannelAggs = async (channelId: string): Promise<ChannelAggsType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/channel/${channelId}/aggs/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const channel = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelAggs', channel);
  }

  return channel;
};

export default loadChannelAggs;
