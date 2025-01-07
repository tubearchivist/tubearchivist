import APIClient from '../../functions/APIClient';

const loadStatsChannel = async () => {
  return APIClient('/api/stats/channel/');
};

export default loadStatsChannel;
