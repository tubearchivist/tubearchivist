import APIClient from '../../functions/APIClient';

const loadStatsDownloadHistory = async () => {
  return APIClient('/api/stats/downloadhist/');
};

export default loadStatsDownloadHistory;
