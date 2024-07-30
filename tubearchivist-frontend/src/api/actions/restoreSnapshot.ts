import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const restoreSnapshot = async (snapshotId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/snapshot/${snapshotId}/`, {
    method: 'POST',
    headers: defaultHeaders,
  });

  const backupRestored = await response.json();

  if (isDevEnvironment()) {
    console.log('restoreSnapshot', backupRestored);
  }

  return backupRestored;
};

export default restoreSnapshot;
