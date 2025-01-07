import APIClient from '../../functions/APIClient';

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
  return APIClient(`/api/task/schedule/${taskName}/`, {
    method: 'POST',
    body: schedule,
  });
};

export default createTaskSchedule;
