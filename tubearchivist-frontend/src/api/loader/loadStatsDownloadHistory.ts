import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadStatsDownloadHistory = async () => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/stats/downloadhist/`, {
    headers: defaultHeaders,
  });

  const notifications = await response.json();

  if (isDevEnvironment()) {
    console.log('loadStatsDownloadHistory', notifications);
  }

  return notifications;
};

export default loadStatsDownloadHistory;
