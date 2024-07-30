import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

const stopTaskByName = async (taskId: string) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/task-id/${taskId}/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },

    body: JSON.stringify({ command: 'stop' }),
  });

  const downloadQueueState = await response.json();
  console.log('stopTaskByName', downloadQueueState);

  return downloadQueueState;
};

export default stopTaskByName;
