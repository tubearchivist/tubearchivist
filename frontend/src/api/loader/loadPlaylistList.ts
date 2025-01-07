import APIClient from '../../functions/APIClient';

type PlaylistType = 'regular' | 'custom';

type LoadPlaylistListProps = {
  channel?: string;
  page?: number | undefined;
  subscribed?: boolean;
  type?: PlaylistType;
};

const loadPlaylistList = async ({ channel, page, subscribed, type }: LoadPlaylistListProps) => {
  const searchParams = new URLSearchParams();

  if (channel) searchParams.append('channel', channel);
  if (page) searchParams.append('page', page.toString());
  if (subscribed) searchParams.append('subscribed', subscribed.toString());
  if (type) searchParams.append('type', type);

  const endpoint = `/api/playlist/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  return APIClient(endpoint);
};

export default loadPlaylistList;
