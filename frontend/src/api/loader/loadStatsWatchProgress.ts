import APIClient from '../../functions/APIClient';

const loadStatsWatchProgress = async () => {
  return APIClient('/api/stats/watch/');
};

export default loadStatsWatchProgress;
