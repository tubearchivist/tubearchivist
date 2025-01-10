import APIClient from '../../functions/APIClient';

export type CookieStateType = {
  cookie_enabled: boolean;
  status?: boolean;
  validated?: number;
  validated_str?: string;
};

const loadCookie = async (): Promise<CookieStateType> => {
  return APIClient('/api/appsettings/cookie/');
};

export default loadCookie;
