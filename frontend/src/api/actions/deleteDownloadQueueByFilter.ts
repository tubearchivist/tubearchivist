import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

type FilterType = 'ignore' | 'pending';

const deleteDownloadQueueByFilter = async (filter: FilterType) => {
  const apiUrl = getApiUrl();

  const searchParams = new URLSearchParams();

  if (filter) {
    searchParams.append('filter', filter);
  }

  const response = await fetch(`${apiUrl}/api/download/?${searchParams.toString()}`, {
    method: 'DELETE',
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const downloadState = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteDownloadQueueByFilter', downloadState);
  }

  return downloadState;
};

export default deleteDownloadQueueByFilter;
