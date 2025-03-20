import APIClient from '../../functions/APIClient';

export type VideoStatsType = {
  doc_count: number;
  media_size: number;
  duration: number;
  duration_str: string;
  type_videos: {
    doc_count: number;
    media_size: number;
    duration: number;
    duration_str: string;
  };
  type_shorts: {
    doc_count: number;
    media_size: number;
    duration: number;
    duration_str: string;
  };
  active_true: {
    doc_count: number;
    media_size: number;
    duration: number;
    duration_str: string;
  };
  active_false: {
    doc_count: number;
    media_size: number;
    duration: number;
    duration_str: string;
  };
  type_streams: {
    doc_count: number;
    media_size: number;
    duration: number;
    duration_str: string;
  };
};

const loadStatsVideo = async () => {
  return APIClient<VideoStatsType>('/api/stats/video/');
};

export default loadStatsVideo;
