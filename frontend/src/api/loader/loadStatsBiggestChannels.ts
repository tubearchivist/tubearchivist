import APIClient from '../../functions/APIClient';

type BiggestChannelsOrderType = 'doc_count' | 'duration' | 'media_size';

const loadStatsBiggestChannels = async (order: BiggestChannelsOrderType) => {
  const searchParams = new URLSearchParams();
  searchParams.append('order', order);

  return APIClient(`/api/stats/biggestchannels/?${searchParams.toString()}`);
};

export default loadStatsBiggestChannels;
