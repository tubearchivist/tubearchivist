import APIClient from '../../functions/APIClient';

export type NotificationPages = 'download' | 'settings' | 'channel' | 'all';

type NotificationType = {
  title: string;
  group: string;
  api_stop: boolean;
  level: string;
  id: string;
  command: boolean | string;
  messages: string[];
  progress: number;
};

export type NotificationResponseType = NotificationType[];

const loadNotifications = async (pageName: NotificationPages, includeReindex = false) => {
  const searchParams = new URLSearchParams();

  if (!includeReindex && pageName !== 'all') {
    searchParams.append('filter', pageName);
  }

  const endpoint = `/api/notification/${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
  return APIClient<NotificationResponseType>(endpoint);
};

export default loadNotifications;
