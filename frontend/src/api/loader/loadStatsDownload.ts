import APIClient from '../../functions/APIClient';

const loadStatsDownload = async () => {
  return APIClient('/api/stats/download/');
};

export default loadStatsDownload;
