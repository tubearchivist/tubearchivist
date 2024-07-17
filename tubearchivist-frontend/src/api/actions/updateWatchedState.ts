import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import deleteVideoProgressById from './deleteVideoProgressById';

export type Watched = {
  id: string;
  is_watched: boolean;
};

const updateWatchedState = async (watched: Watched) => {
  const apiUrl = getApiUrl();

  if (watched.is_watched) {
    await deleteVideoProgressById(watched.id);
  }

  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/watched/`, {
    method: 'POST',
    headers,

    body: JSON.stringify(watched),
  });

  const watchedState = await response.json();
  console.log('updateWatchedState', watchedState);

  return watchedState;
};

export default updateWatchedState;
