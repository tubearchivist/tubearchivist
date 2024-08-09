import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteDownloadById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/download/${youtubeId}/`, {
    method: 'DELETE',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
  });

  const downloadState = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteDownloadById', downloadState);
  }

  return downloadState;
};

export default deleteDownloadById;
