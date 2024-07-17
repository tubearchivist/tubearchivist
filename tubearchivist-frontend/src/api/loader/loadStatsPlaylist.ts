import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadStatsPlaylist = async () => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/stats/playlist/`, {
    headers,
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadStatsPlaylist', notifications);
  }

  return notifications;
};

export default loadStatsPlaylist;
