import APIClient from '../../functions/APIClient';
import { CookieStateType } from '../loader/loadCookie';

const updateCookie = async (cookie: string) => {
  return APIClient<CookieStateType>('/api/appsettings/cookie/', {
    method: 'PUT',
    body: { cookie },
  });
};

export default updateCookie;
