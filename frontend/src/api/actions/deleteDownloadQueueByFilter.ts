import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

type FilterType = 'ignore' | 'pending';

const deleteDownloadQueueByFilter = async (filter: FilterType) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const searchParams = new URLSearchParams();

  if (filter) {
    searchParams.append('filter', filter);
  }

  const response = await fetch(`${apiUrl}/api/download/?${searchParams.toString()}`, {
    method: 'DELETE',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
  });

  const downloadState = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteDownloadQueueByFilter', downloadState);
  }

  return downloadState;
};

export default deleteDownloadQueueByFilter;
