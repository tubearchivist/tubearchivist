import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const restoreSnapshot = async (snapshotId: string) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/appsettings/snapshot/${snapshotId}/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
  });

  const backupRestored = await response.json();

  if (isDevEnvironment()) {
    console.log('restoreSnapshot', backupRestored);
  }

  return backupRestored;
};

export default restoreSnapshot;
