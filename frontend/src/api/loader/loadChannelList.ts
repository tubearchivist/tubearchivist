import APIClient from '../../functions/APIClient';

const loadChannelList = async (page: number, showSubscribed: boolean) => {
  const searchParams = new URLSearchParams();

  if (page) searchParams.append('page', page.toString());
  if (showSubscribed) searchParams.append('filter', 'subscribed');

  const endpoint = `/api/channel/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;

  return APIClient(endpoint);
};

export default loadChannelList;
