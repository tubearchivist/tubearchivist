import APIClient from '../../functions/APIClient';
import { CookieStateType } from '../loader/loadCookie';

const deleteCookie = async (): Promise<CookieStateType> => {
  return APIClient('/api/appsettings/cookie/', {
    method: 'DELETE',
  });
};

export default deleteCookie;
