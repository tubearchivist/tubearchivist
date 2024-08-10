import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

export type ChannelNavResponseType = {
  has_streams: boolean;
  has_shorts: boolean;
  has_playlists: boolean;
  has_pending: boolean;
};

const loadChannelNav = async (youtubeChannelId: string): Promise<ChannelNavResponseType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/channel/${youtubeChannelId}/nav/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const channel = await response.json();

  if (isDevEnvironment()) {
    console.log('loadChannelNav', channel);
  }

  return channel;
};

export default loadChannelNav;
