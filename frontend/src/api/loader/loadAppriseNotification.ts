import APIClient from '../../functions/APIClient';

export type AppriseNotificationType = {
  check_reindex?: {
    urls: string[];
    title: string;
  };
  download_pending?: {
    urls: string[];
    title: string;
  };
  extract_download?: {
    urls: string[];
    title: string;
  };
  update_subscribed?: {
    urls: string[];
    title: string;
  };
};

const loadAppriseNotification = async () => {
  return APIClient<AppriseNotificationType>('/api/task/notification/');
};

export default loadAppriseNotification;
