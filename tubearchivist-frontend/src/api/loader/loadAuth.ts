import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

const loadAuth = async () => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/ping/`, {
    headers,
  });

  return response;
};

export default loadAuth;
