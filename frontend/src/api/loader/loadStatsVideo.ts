import APIClient from '../../functions/APIClient';

const loadStatsVideo = async () => {
  return APIClient('/api/stats/video/');
};

export default loadStatsVideo;
