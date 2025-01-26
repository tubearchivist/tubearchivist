import APIClient from '../../functions/APIClient';

const deleteVideo = async (videoId: string) => {
  return APIClient(`/api/video/${videoId}/`, {
    method: 'DELETE',
  });
};

export default deleteVideo;
