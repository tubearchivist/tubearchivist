import APIClient from '../../functions/APIClient';
import { UserAccountType } from '../../pages/Base';

const loadUserAccount = async (): Promise<UserAccountType> => {
  return APIClient('/api/user/account/');
};

export default loadUserAccount;
