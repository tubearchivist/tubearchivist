import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const queueBackup = async () => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/backup/`, {
    method: 'POST',
    headers,
  });

  const backupQueued = await response.json();

  if (isDevEnvironment()) {
    console.log('queueBackup', backupQueued);
  }

  return backupQueued;
};

export default queueBackup;
