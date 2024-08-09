import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteVideoProgressById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/progress/`, {
    method: 'DELETE',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
  });

  const watchedState = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteVideoProgressById', watchedState);
  }

  return watchedState;
};

export default deleteVideoProgressById;
