import { UserConfigType } from '../actions/updateUserConfig';
import APIClient from '../../functions/APIClient';

const loadUserMeConfig = async (): Promise<UserConfigType> => {
  return APIClient('/api/user/me/');
};

export default loadUserMeConfig;
