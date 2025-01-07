import APIClient from '../../functions/APIClient';

const deleteVideoProgressById = async (youtubeId: string) => {
  return APIClient(`/api/video/${youtubeId}/progress/`, {
    method: 'DELETE',
  });
};

export default deleteVideoProgressById;
