import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

export type DownloadQueueStatus = 'ignore' | 'pending' | 'priority';

const updateDownloadQueueStatusById = async (youtubeId: string, status: DownloadQueueStatus) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/download/${youtubeId}/`, {
    method: 'POST',
    headers: defaultHeaders,

    body: JSON.stringify({
      status,
    }),
  });

  const downloadQueueState = await response.json();
  console.log('updateDownloadQueueStatusById', downloadQueueState);

  return downloadQueueState;
};

export default updateDownloadQueueStatusById;
