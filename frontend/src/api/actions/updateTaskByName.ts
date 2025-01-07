import APIClient from '../../functions/APIClient';

type TaskNamesType =
  | 'download_pending'
  | 'update_subscribed'
  | 'manual_import'
  | 'resync_thumbs'
  | 'rescan_filesystem';

const updateTaskByName = async (taskName: TaskNamesType) => {
  return APIClient(`/api/task/by-name/${taskName}/`, {
    method: 'POST',
  });
};

export default updateTaskByName;
