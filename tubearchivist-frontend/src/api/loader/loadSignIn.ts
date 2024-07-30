import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';

export type LoginResponseType = {
  token?: string;
  user_id: number;
  is_superuser: boolean;
  is_staff: boolean;
  user_groups: [];
};

const loadSignIn = async (username: string, password: string, saveLogin: boolean) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/login/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      Authorization: 'Basic ' + btoa(username + ':' + password),
    },
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

export default loadSignIn;
