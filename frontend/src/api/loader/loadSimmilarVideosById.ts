import APIClient from '../../functions/APIClient';

const loadSimmilarVideosById = async (youtubeId: string) => {
  return APIClient(`/api/video/${youtubeId}/similar/`);
};

export default loadSimmilarVideosById;
