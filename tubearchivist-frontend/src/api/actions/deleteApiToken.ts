import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const deleteApiToken = async () => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/token/`, {
    method: 'DELETE',
    headers,
  });

  const resetToken = await response.json();
  if (isDevEnvironment()) {
    console.log('deleteApiToken', resetToken);
  }

  return resetToken;
};

export default deleteApiToken;
