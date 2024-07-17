import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

export type NotificationPages = 'download' | 'settings' | 'channel' | 'all';

const loadNotifications = async (pageName: NotificationPages, includeReindex = false) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  let params = '';
  if (!includeReindex && pageName !== 'all') {
    params = `?filter=${pageName}`;
  }

  const response = await fetch(`${apiUrl}/api/notification/${params}`, {
    headers,
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadNotifications', notifications);
  }

  return notifications;
};

export default loadNotifications;
