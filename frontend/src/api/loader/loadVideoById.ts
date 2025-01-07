import APIClient from '../../functions/APIClient';
import { VideoResponseType } from '../../pages/Video';

const loadVideoById = async (youtubeId: string): Promise<VideoResponseType> => {
  return APIClient(`/api/video/${youtubeId}/`);
};

export default loadVideoById;
