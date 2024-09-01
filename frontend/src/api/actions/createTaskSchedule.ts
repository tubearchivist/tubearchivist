import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

export type TaskScheduleNameType =
  | 'update_subscribed'
  | 'download_pending'
  | 'extract_download'
  | 'check_reindex'
  | 'manual_import'
  | 'run_backup'
  | 'restore_backup'
  | 'rescan_filesystem'
  | 'thumbnail_check'
  | 'resync_thumbs'
  | 'index_playlists'
  | 'subscribe_to'
  | 'version_check';

type ScheduleConfigType = {
  schedule?: string;
  config?: {
    days?: number;
    rotate?: number;
  };
};

const createTaskSchedule = async (taskName: TaskScheduleNameType, schedule: ScheduleConfigType) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/task/schedule/${taskName}/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
    body: JSON.stringify(schedule),
  });

  const scheduledTask = await response.json();

  if (isDevEnvironment()) {
    console.log('createTaskSchedule', scheduledTask);
  }

  return scheduledTask;
};

export default createTaskSchedule;
