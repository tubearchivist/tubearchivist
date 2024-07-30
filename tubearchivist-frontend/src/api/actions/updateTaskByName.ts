import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

type TaskNamesType =
  | 'download_pending'
  | 'update_subscribed'
  | 'manual_import'
  | 'resync_thumbs'
  | 'rescan_filesystem';

const updateTaskByName = async (taskName: TaskNamesType) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/task-name/${taskName}/`, {
    method: 'POST',
    headers: defaultHeaders,
  });

  const downloadQueueState = await response.json();
  console.log('updateTaskByName', downloadQueueState);

  return downloadQueueState;
};

export default updateTaskByName;
