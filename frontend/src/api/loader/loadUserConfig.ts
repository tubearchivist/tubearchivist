import { UserMeType } from '../actions/updateUserConfig';
import APIClient from '../../functions/APIClient';

const loadUserMeConfig = async (): Promise<UserMeType> => {
  return APIClient('/api/user/me/');
};

export default loadUserMeConfig;
