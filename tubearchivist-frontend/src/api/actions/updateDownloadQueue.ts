import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

const updateDownloadQueue = async (download: string, autostart: boolean) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  let params = '';
  if (autostart) {
    params = '?autostart=true';
  }

  const response = await fetch(`${apiUrl}/api/download/${params}`, {
    method: 'POST',
    headers,

    body: JSON.stringify({
      data: [{ youtube_id: download, status: 'pending' }],
    }),
  });

  const downloadState = await response.json();
  console.log('updateDownloadQueue', downloadState);

  return downloadState;
};

export default updateDownloadQueue;
