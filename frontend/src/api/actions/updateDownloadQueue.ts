import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';

const updateDownloadQueue = async (youtubeIdStrings: string, autostart: boolean) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const urls = [];
  const containsMultiple = youtubeIdStrings.includes('\n');

  if (containsMultiple) {
    const youtubeIds = youtubeIdStrings.split('\n');

    youtubeIds.forEach(youtubeId => {
      urls.push({ youtube_id: youtubeId, status: 'pending' });
    });
  } else {
    urls.push({ youtube_id: youtubeIdStrings, status: 'pending' });
  }

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
    credentials: getFetchCredentials(),

    body: JSON.stringify({
      data: [...urls],
    }),
  });

  const downloadState = await response.json();
  console.log('updateDownloadQueue', downloadState);

  return downloadState;
};

export default updateDownloadQueue;
