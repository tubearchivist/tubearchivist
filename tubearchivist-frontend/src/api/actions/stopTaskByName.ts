import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

const stopTaskByName = async (taskId: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/task-id/${taskId}/`, {
    method: 'POST',
    headers: defaultHeaders,

    body: JSON.stringify({ command: 'stop' }),
  });

  const downloadQueueState = await response.json();
  console.log('stopTaskByName', downloadQueueState);

  return downloadQueueState;
};

export default stopTaskByName;
