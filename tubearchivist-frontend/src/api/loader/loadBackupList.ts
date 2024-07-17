import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadBackupList = async () => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/backup/`, {
    headers,
  });

  const backupList = await response.json();

  if (isDevEnvironment()) {
    console.log('loadBackupList', backupList);
  }

  return backupList;
};

export default loadBackupList;
