import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const queueBackup = async () => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/backup/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
  });

  const backupQueued = await response.json();

  if (isDevEnvironment()) {
    console.log('queueBackup', backupQueued);
  }

  return backupQueued;
};

export default queueBackup;
