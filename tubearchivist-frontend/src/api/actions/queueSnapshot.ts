import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const queueSnapshot = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/snapshot/`, {
    method: 'POST',
    headers: defaultHeaders,
  });

  const snapshotQueued = await response.json();

  if (isDevEnvironment()) {
    console.log('queueSnapshot', snapshotQueued);
  }

  return snapshotQueued;
};

export default queueSnapshot;
