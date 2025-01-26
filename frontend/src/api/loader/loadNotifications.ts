import APIClient from '../../functions/APIClient';

export type NotificationPages = 'download' | 'settings' | 'channel' | 'all';

const loadNotifications = async (pageName: NotificationPages, includeReindex = false) => {
  const searchParams = new URLSearchParams();

  if (!includeReindex && pageName !== 'all') {
    searchParams.append('filter', pageName);
  }

  const endpoint = `/api/notification/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  return APIClient(endpoint);
};

export default loadNotifications;
