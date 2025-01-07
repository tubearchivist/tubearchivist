import APIClient from '../../functions/APIClient';

export type DownloadQueueStatus = 'ignore' | 'pending' | 'priority';

const updateDownloadQueueStatusById = async (youtubeId: string, status: DownloadQueueStatus) => {
  return APIClient(`/api/download/${youtubeId}/`, {
    method: 'POST',
    body: { status: status },
  });
};

export default updateDownloadQueueStatusById;
