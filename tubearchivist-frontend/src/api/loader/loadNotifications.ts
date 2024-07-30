import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

export type NotificationPages = 'download' | 'settings' | 'channel' | 'all';

const loadNotifications = async (pageName: NotificationPages, includeReindex = false) => {
  const apiUrl = getApiUrl();

  let params = '';
  if (!includeReindex && pageName !== 'all') {
    params = `?filter=${pageName}`;
  }

  const response = await fetch(`${apiUrl}/api/notification/${params}`, {
    headers: defaultHeaders,
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadNotifications', notifications);
  }

  return notifications;
};

export default loadNotifications;
