import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';

type ValidatedCookieType = {
  cookie_enabled: boolean;
  status: boolean;
  validated: number;
  validated_str: string;
};

const updateCookie = async (): Promise<ValidatedCookieType> => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  headers.append('Content-Type', 'application/json');

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/cookie/`, {
    method: 'POST',
    headers,
  });

  const validatedCookie = await response.json();
  console.log('updateCookie', validatedCookie);

  return validatedCookie;
};

export default updateCookie;
