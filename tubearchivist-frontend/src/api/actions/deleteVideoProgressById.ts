import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteVideoProgressById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/progress/`, {
    method: 'DELETE',
    headers,
  });

  const watchedState = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteVideoProgressById', watchedState);
  }

  return watchedState;
};

export default deleteVideoProgressById;
