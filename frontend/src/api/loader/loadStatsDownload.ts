import APIClient from '../../functions/APIClient';

export type DownloadStatsType = {
  pending: number;
  pending_videos: number;
  pending_shorts: number;
  pending_streams: number;
};

const loadStatsDownload = async () => {
  return APIClient<DownloadStatsType>('/api/stats/download/');
};

export default loadStatsDownload;
