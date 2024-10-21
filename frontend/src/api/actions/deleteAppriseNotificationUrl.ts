import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

type AppriseTaskNameType =
  | 'update_subscribed'
  | 'extract_download'
  | 'download_pending'
  | 'check_reindex';

const deleteAppriseNotificationUrl = async (taskName: AppriseTaskNameType) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/task/notification/`, {
    method: 'DELETE',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
    body: JSON.stringify({ task_name: taskName }),
  });

  const appriseNotification = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteAppriseNotificationUrl', appriseNotification);
  }

  return appriseNotification;
};

export default deleteAppriseNotificationUrl;
