import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteVideoProgressById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/video/${youtubeId}/progress/`, {
    method: 'DELETE',
    headers: defaultHeaders,
  });

  const watchedState = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteVideoProgressById', watchedState);
  }

  return watchedState;
};

export default deleteVideoProgressById;
