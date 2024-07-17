import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteDownloadById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/download/${youtubeId}/`, {
    method: 'DELETE',
    headers,
  });

  const downloadState = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteDownloadById', downloadState);
  }

  return downloadState;
};

export default deleteDownloadById;
