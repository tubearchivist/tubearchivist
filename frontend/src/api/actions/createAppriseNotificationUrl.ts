import APIClient from '../../functions/APIClient';

export type AppriseTaskNameType =
  | 'update_subscribed'
  | 'extract_download'
  | 'download_pending'
  | 'check_reindex';

const createAppriseNotificationUrl = async (taskName: AppriseTaskNameType, url: string) => {
  return APIClient('/api/task/notification/', {
    method: 'POST',
    body: { task_name: taskName, url },
  });
};

export default createAppriseNotificationUrl;
