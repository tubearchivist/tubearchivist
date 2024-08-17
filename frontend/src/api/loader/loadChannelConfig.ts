import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';
import { ChannelAboutConfigType } from '../actions/updateChannelSettings';

const loadChannelConfig = async (channelId: string): Promise<ChannelAboutConfigType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/channel/${channelId}/about/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const channel = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelConfig', channel);
  }

  return channel;
};

export default loadChannelConfig;
