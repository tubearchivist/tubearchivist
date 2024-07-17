import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const queueSnapshot = async () => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/snapshot/`, {
    method: 'POST',
    headers,
  });

  const snapshotQueued = await response.json();

  if (isDevEnvironment()) {
    console.log('queueSnapshot', snapshotQueued);
  }

  return snapshotQueued;
};

export default queueSnapshot;
