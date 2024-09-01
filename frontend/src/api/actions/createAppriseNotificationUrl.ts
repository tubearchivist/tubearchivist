import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

export type AppriseTaskNameType =
  | 'update_subscribed'
  | 'extract_download'
  | 'download_pending'
  | 'check_reindex';

const createAppriseNotificationUrl = async (taskName: AppriseTaskNameType, url: string) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/task/notification/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
    body: JSON.stringify({ task_name: taskName, url }),
  });

  const appriseNotificationUrl = await response.json();

  if (isDevEnvironment()) {
    console.log('createAppriseNotificationUrl', appriseNotificationUrl);
  }

  return appriseNotificationUrl;
};

export default createAppriseNotificationUrl;
