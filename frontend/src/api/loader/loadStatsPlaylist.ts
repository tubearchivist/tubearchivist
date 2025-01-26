import APIClient from '../../functions/APIClient';

const loadStatsPlaylist = async () => {
  return APIClient('/api/stats/playlist/');
};

export default loadStatsPlaylist;
