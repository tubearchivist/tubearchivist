import defaultHeaders from '../../configuration/defaultHeaders';
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
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/appsettings/cookie/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
  });

  const validatedCookie = await response.json();
  console.log('updateCookie', validatedCookie);

  return validatedCookie;
};

export default updateCookie;
