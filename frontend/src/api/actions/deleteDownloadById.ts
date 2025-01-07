import APIClient from '../../functions/APIClient';

const deleteDownloadById = async (youtubeId: string) => {
  return APIClient(`/api/download/${youtubeId}/`, {
    method: 'DELETE',
  });
};

export default deleteDownloadById;
