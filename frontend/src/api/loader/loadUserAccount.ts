import APIClient from '../../functions/APIClient';

export type UserAccountType = {
  id: number;
  name: string;
  is_superuser: boolean;
  is_staff: boolean;
  groups: [];
  user_permissions: [];
  last_login: string;
};

const loadUserAccount = async (): Promise<UserAccountType> => {
  return APIClient('/api/user/account/');
};

export default loadUserAccount;
