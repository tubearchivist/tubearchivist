import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
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

  const response = await fetch(`${apiUrl}/api/watched/`, {
    method: 'POST',
    headers: defaultHeaders,

    body: JSON.stringify(watched),
  });

  const watchedState = await response.json();
  console.log('updateWatchedState', watchedState);

  return watchedState;
};

export default updateWatchedState;
