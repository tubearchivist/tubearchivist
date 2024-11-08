import { UserMeType } from '../api/actions/updateUserConfig';

const loadIsAdmin = (config: UserMeType) => {
  const isAdmin = config.is_staff || config.is_superuser;

  return isAdmin;
};

export default loadIsAdmin;
