import APIClient from '../../functions/APIClient';

export type PlaylistStatsType = {
  doc_count: number;
  active_false: number;
  active_true: number;
  subscribed_true: number;
};

const loadStatsPlaylist = async () => {
  return APIClient<PlaylistStatsType>('/api/stats/playlist/');
};

export default loadStatsPlaylist;
