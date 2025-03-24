import APIClient from '../../functions/APIClient';
import { VideoType } from '../../pages/Home';

export type VideoResponseType = VideoType;

const loadVideoById = async (youtubeId: string) => {
  return APIClient<VideoResponseType>(`/api/video/${youtubeId}/`);
};

export default loadVideoById;
