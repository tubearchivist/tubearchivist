import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteDownloadById = async (youtubeId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/download/${youtubeId}/`, {
    method: 'DELETE',
    headers: defaultHeaders,
  });

  const downloadState = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteDownloadById', downloadState);
  }

  return downloadState;
};

export default deleteDownloadById;
