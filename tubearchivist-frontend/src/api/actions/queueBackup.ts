import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const queueBackup = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/backup/`, {
    method: 'POST',
    headers: defaultHeaders,
  });

  const backupQueued = await response.json();

  if (isDevEnvironment()) {
    console.log('queueBackup', backupQueued);
  }

  return backupQueued;
};

export default queueBackup;
