import { useUserConfigStore } from '../stores/UserConfigStore';

const useIsAdmin = () => {
  const { userConfig } = useUserConfigStore();
  const isAdmin = userConfig?.is_staff || userConfig?.is_superuser;

  return isAdmin;
};

export default useIsAdmin;
