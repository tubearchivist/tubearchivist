import { SortByType, SortOrderType, ViewLayoutType } from '../../pages/Home';
import getApiUrl from '../../configuration/getApiUrl';
import defaultHeaders from '../../configuration/defaultHeaders';
import getCookie from '../../functions/getCookie';
import getFetchCredentials from '../../configuration/getFetchCredentials';

export type UserMeType = {
  id: number;
  name: string;
  is_superuser: boolean;
  is_staff: boolean;
  groups: [];
  user_permissions: [];
  last_login: string;
  config: UserConfigType;
};

export type ColourVariants = 'dark.css' | 'light.css' | 'matrix.css' | 'midnight.css';

export type UserConfigType = {
  stylesheet: ColourVariants;
  page_size: number;
  sort_by: SortByType;
  sort_order: SortOrderType;
  view_style_home: ViewLayoutType;
  view_style_channel: ViewLayoutType;
  view_style_downloads: ViewLayoutType;
  view_style_playlist: ViewLayoutType;
  grid_items: number;
  hide_watched: boolean;
  show_ignored_only: boolean;
  show_subed_only: boolean;
};

const updateUserConfig = async (config: Partial<UserConfigType>): Promise<UserConfigType> => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/user/me/`, {
    method: 'POST',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),

    body: JSON.stringify({ config }),
  });

  const userConfig = await response.json();
  console.log('updateUserConfig', userConfig);

  return userConfig;
};

export default updateUserConfig;
