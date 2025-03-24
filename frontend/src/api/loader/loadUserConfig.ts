import { UserConfigType } from '../actions/updateUserConfig';
import APIClient from '../../functions/APIClient';

const loadUserMeConfig = async () => {
  return APIClient<UserConfigType>('/api/user/me/');
};

export default loadUserMeConfig;
