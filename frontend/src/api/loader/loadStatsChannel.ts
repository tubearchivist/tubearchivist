import APIClient from '../../functions/APIClient';

export type ChannelStatsType = {
  doc_count: number;
  active_true: number;
  subscribed_true: number;
};

const loadStatsChannel = async () => {
  return APIClient<ChannelStatsType>('/api/stats/channel/');
};

export default loadStatsChannel;
