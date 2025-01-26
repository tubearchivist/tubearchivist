import APIClient from '../../functions/APIClient';
import { CookieStateType } from '../loader/loadCookie';

const updateCookie = async (cookie: string): Promise<CookieStateType> => {
  return APIClient('/api/appsettings/cookie/', {
    method: 'PUT',
    body: { cookie },
  });
};

export default updateCookie;
