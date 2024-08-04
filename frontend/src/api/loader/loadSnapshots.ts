import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadSnapshots = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/appsettings/snapshot/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const backupList = await response.json();

  if (isDevEnvironment()) {
    console.log('loadSnapshots', backupList);
  }

  return backupList;
};

export default loadSnapshots;
