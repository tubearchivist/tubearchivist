import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

const updateDownloadQueue = async (download: string, autostart: boolean) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  let params = '';
  if (autostart) {
    params = '?autostart=true';
  }

  const response = await fetch(`${apiUrl}/api/download/${params}`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },

    body: JSON.stringify({
      data: [{ youtube_id: download, status: 'pending' }],
    }),
  });

  const downloadState = await response.json();
  console.log('updateDownloadQueue', downloadState);

  return downloadState;
};

export default updateDownloadQueue;
