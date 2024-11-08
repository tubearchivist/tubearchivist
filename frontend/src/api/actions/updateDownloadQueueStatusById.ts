import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';

export type DownloadQueueStatus = 'ignore' | 'pending' | 'priority';

const updateDownloadQueueStatusById = async (youtubeId: string, status: DownloadQueueStatus) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/download/${youtubeId}/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),

    body: JSON.stringify({
      status,
    }),
  });

  const downloadQueueState = await response.json();
  console.log('updateDownloadQueueStatusById', downloadQueueState);

  return downloadQueueState;
};

export default updateDownloadQueueStatusById;
