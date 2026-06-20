import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';

export type OidcInfoType = {
  enabled: boolean;
  local_login: boolean;
  label: string;
  login_url: string;
};

const loadOidcInfo = async (): Promise<OidcInfoType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/user/oidc/`, {
    headers: { ...defaultHeaders },
    credentials: getFetchCredentials(),
  });

  if (!response.ok) {
    throw new Error(`OIDC info request failed: ${response.status}`);
  }

  return response.json();
};

export default loadOidcInfo;
