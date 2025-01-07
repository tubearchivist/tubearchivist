import APIClient from '../../functions/APIClient';

export type ValidatedCookieType = {
  cookie_enabled: boolean;
  status: boolean;
  validated: number;
  validated_str: string;
  cookie_validated?: boolean;
};

const updateCookie = async (): Promise<ValidatedCookieType> => {
  return APIClient('/api/appsettings/cookie/', {
    method: 'POST',
  });
};

export default updateCookie;
