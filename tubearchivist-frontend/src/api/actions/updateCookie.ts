import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

type ValidatedCookieType = {
  cookie_enabled: boolean;
  status: boolean;
  validated: number;
  validated_str: string;
};

const updateCookie = async (): Promise<ValidatedCookieType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/cookie/`, {
    method: 'POST',
    headers: defaultHeaders,
  });

  const validatedCookie = await response.json();
  console.log('updateCookie', validatedCookie);

  return validatedCookie;
};

export default updateCookie;
