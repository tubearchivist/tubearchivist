import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

type PlaylistType = 'regular' | 'custom';

type LoadPlaylistListProps = {
  channel?: string;
  page?: number | undefined;
  subscribed?: boolean;
  type?: PlaylistType;
};

const loadPlaylistList = async ({ channel, page, subscribed, type }: LoadPlaylistListProps) => {
  const apiUrl = getApiUrl();

  const searchParams = new URLSearchParams();

  if (channel) {
    searchParams.append('channel', channel);
  }

  if (page) {
    searchParams.append('page', page.toString());
  }

  if (subscribed) {
    searchParams.append('subscribed', subscribed.toString());
  }

  if (type) {
    searchParams.append('type', type);
  }

  const response = await fetch(`${apiUrl}/api/playlist/?${searchParams.toString()}`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const playlist = await response.json();

  if (isDevEnvironment()) {
    console.log('loadPlaylistList', playlist);
  }

  return playlist;
};

export default loadPlaylistList;
