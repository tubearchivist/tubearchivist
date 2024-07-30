import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

const updateDownloadQueue = async (download: string, autostart: boolean) => {
  const apiUrl = getApiUrl();

  let params = '';
  if (autostart) {
    params = '?autostart=true';
  }

  const response = await fetch(`${apiUrl}/api/download/${params}`, {
    method: 'POST',
    headers: defaultHeaders,

    body: JSON.stringify({
      data: [{ youtube_id: download, status: 'pending' }],
    }),
  });

  const downloadState = await response.json();
  console.log('updateDownloadQueue', downloadState);

  return downloadState;
};

export default updateDownloadQueue;
