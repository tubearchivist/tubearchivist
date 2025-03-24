import APIClient from '../../functions/APIClient';
import { VideoResponseType } from './loadVideoById';

const loadSimilarVideosById = async (youtubeId: string) => {
  return APIClient<VideoResponseType[]>(`/api/video/${youtubeId}/similar/`);
};

export default loadSimilarVideosById;
