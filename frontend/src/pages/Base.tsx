import { Outlet, useLoaderData, useSearchParams } from 'react-router-dom';
import Footer from '../components/Footer';
import Colours from '../configuration/colours/Colours';
import { UserConfigType } from '../api/actions/updateUserConfig';
import { useCallback, useEffect } from 'react';
import Navigation from '../components/Navigation';
import { useAuthStore } from '../stores/AuthDataStore';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { useUserAccountStore } from '../stores/UserAccountStore';
import { UserAccountType } from '../api/loader/loadUserAccount';
import { useAppSettingsStore } from '../stores/AppSettingsStore';
import { AppSettingsConfigType } from '../api/loader/loadAppsettingsConfig';

type TaUpdateType = {
  version?: string;
  is_breaking?: boolean;
};

export type AuthenticationType = {
  response: string;
  user: number;
  version: string;
  ta_update: TaUpdateType;
};

type BaseLoaderData = {
  userConfig: UserConfigType;
  userAccount: UserAccountType;
  appSettings: AppSettingsConfigType;
  auth: AuthenticationType;
};

export type OutletContextType = {
  currentPage: number;
  setCurrentPage: (page: number) => void;
};

const Base = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { setAuth } = useAuthStore();
  const { setUserConfig } = useUserConfigStore();
  const { setUserAccount } = useUserAccountStore();
  const { setAppSettingsConfig } = useAppSettingsStore();

  const { userConfig, userAccount, appSettings, auth } = useLoaderData() as BaseLoaderData;
  const currentPageFromUrl = Number(searchParams.get('page'));
  const currentPage = Number.isNaN(currentPageFromUrl) ? 0 : currentPageFromUrl;

  useEffect(() => {
    setAuth(auth);
    setUserConfig(userConfig);
    setUserAccount(userAccount);
    setAppSettingsConfig(appSettings);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setCurrentPage = useCallback(
    (page: number) => {
      setSearchParams(params => {
        if (page === 0) {
          params.delete('page');
        } else {
          params.set('page', page.toString());
        }

        return params;
      });
    },
    [setSearchParams],
  );

  return (
    <>
      <Colours />
      <div className="main-content">
        <Navigation />
        {/** Outlet: https://reactrouter.com/en/main/components/outlet */}
        <Outlet context={{ currentPage, setCurrentPage }} />
      </div>
      <Footer />
    </>
  );
};

export default Base;
