import APIClient from '../../functions/APIClient';

type DownloadHistoryType = {
  date: string;
  count: number;
  media_size: number;
};

export type DownloadHistoryStatsType = DownloadHistoryType[];

const loadStatsDownloadHistory = async () => {
  return APIClient<DownloadHistoryStatsType>('/api/stats/downloadhist/');
};

export default loadStatsDownloadHistory;
