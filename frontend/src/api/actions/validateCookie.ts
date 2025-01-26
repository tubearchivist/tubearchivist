import APIClient from '../../functions/APIClient';
import { CookieStateType } from '../loader/loadCookie';

const validateCookie = async (): Promise<CookieStateType> => {
  return APIClient('/api/appsettings/cookie/', {
    method: 'POST',
  });
};

export default validateCookie;
