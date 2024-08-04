import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import deleteVideoProgressById from './deleteVideoProgressById';

export type Watched = {
  id: string;
  is_watched: boolean;
};

const updateWatchedState = async (watched: Watched) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  if (watched.is_watched) {
    await deleteVideoProgressById(watched.id);
  }

  const response = await fetch(`${apiUrl}/api/watched/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },

    body: JSON.stringify(watched),
  });

  const watchedState = await response.json();
  console.log('updateWatchedState', watchedState);

  return watchedState;
};

export default updateWatchedState;
