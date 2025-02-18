import { useUserAccountStore } from '../stores/UserAccountStore';

const useIsAdmin = () => {
  const { userAccount } = useUserAccountStore();
  const isAdmin = userAccount?.is_staff || userAccount?.is_superuser;

  return isAdmin;
};

export default useIsAdmin;
