import APIClient from '../../functions/APIClient';

const logOut = async () => {
  return APIClient('/api/user/logout/', {
    method: 'POST',
  });
};

export default logOut;
