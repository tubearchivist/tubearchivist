import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';

const loadAuth = async () => {
  // works differently, return response to check for status in main.tsx
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/ping/`, {
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
  });

  return response;
};

export default loadAuth;
