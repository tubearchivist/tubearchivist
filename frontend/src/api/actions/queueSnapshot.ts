import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const queueSnapshot = async () => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/snapshot/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
  });

  const snapshotQueued = await response.json();

  if (isDevEnvironment()) {
    console.log('queueSnapshot', snapshotQueued);
  }

  return snapshotQueued;
};

export default queueSnapshot;
