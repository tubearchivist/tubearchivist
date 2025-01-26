import APIClient from '../../functions/APIClient';

const loadCommentsbyVideoId = async (youtubeId: string) => {
  return APIClient(`/api/video/${youtubeId}/comment/`);
};

export default loadCommentsbyVideoId;
