import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

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

const loadAppriseNotification = async (): Promise<AppriseNotificationType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/task/notification/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const notification = await response.json();

  if (isDevEnvironment()) {
    console.log('loadAppriseNotification', notification);
  }

  return notification;
};

export default loadAppriseNotification;
