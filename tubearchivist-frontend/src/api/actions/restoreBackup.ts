import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const restoreBackup = async (fileName: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/backup/${fileName}/`, {
    method: 'POST',
    headers: defaultHeaders,
  });

  const backupRestored = await response.json();

  if (isDevEnvironment()) {
    console.log('restoreBackup', backupRestored);
  }

  return backupRestored;
};

export default restoreBackup;
