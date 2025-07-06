import APIClient from '../../functions/APIClient';

type AppriseTaskNameType =
  | 'update_subscribed'
  | 'extract_download'
  | 'download_pending'
  | 'check_reindex';

const deleteAppriseNotificationUrl = async (taskName: AppriseTaskNameType, url: string) => {
  return APIClient('/api/task/notification/', {
    method: 'DELETE',
    body: { task_name: taskName, url: url },
  });
};

export default deleteAppriseNotificationUrl;
