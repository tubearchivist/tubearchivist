import APIClient from '../../functions/APIClient';

export type WatchProgressStatsType = {
  total: {
    duration: number;
    duration_str: string;
    items: number;
  };
  unwatched: {
    duration: number;
    duration_str: string;
    progress: number;
    items: number;
  };
  watched: {
    duration: number;
    duration_str: string;
    progress: number;
    items: number;
  };
};

const loadStatsWatchProgress = async () => {
  return APIClient<WatchProgressStatsType>('/api/stats/watch/');
};

export default loadStatsWatchProgress;
