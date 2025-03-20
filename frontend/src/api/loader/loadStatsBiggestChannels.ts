import APIClient from '../../functions/APIClient';

type BiggestChannelsOrderType = 'doc_count' | 'duration' | 'media_size';

type BiggestChannelsType = {
  id: string;
  name: string;
  doc_count: number;
  duration: number;
  duration_str: string;
  media_size: number;
};

export type BiggestChannelsStatsType = BiggestChannelsType[];

const loadStatsBiggestChannels = async (order: BiggestChannelsOrderType) => {
  const searchParams = new URLSearchParams();
  searchParams.append('order', order);

  return APIClient<BiggestChannelsStatsType>(
    `/api/stats/biggestchannels/?${searchParams.toString()}`,
  );
};

export default loadStatsBiggestChannels;
