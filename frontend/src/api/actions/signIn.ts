import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';

export type LoginResponseType = {
  token?: string;
  user_id: number;
  is_superuser: boolean;
  is_staff: boolean;
  user_groups: [];
};

const signIn = async (username: string, password: string, saveLogin: boolean) => {
  // works differently, response status is checked
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/user/login/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
    body: JSON.stringify({
      username,
      password,
      remember_me: saveLogin ? 'on' : 'off',
    }),
  });

  if (response.status === 403) {
    console.log('Might be already logged in.', await response.json());
  }

  return response;
};

export default signIn;
