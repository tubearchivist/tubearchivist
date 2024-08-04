import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadBackupList = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/appsettings/backup/`, {
    headers: defaultHeaders,
  });

  const backupList = await response.json();

  if (isDevEnvironment()) {
    console.log('loadBackupList', backupList);
  }

  return backupList;
};

export default loadBackupList;
