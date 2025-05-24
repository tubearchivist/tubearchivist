import { Outlet, useLoaderData, useLocation, useSearchParams } from 'react-router-dom';
import Footer from '../components/Footer';
import Colours from '../configuration/colours/Colours';
import { UserConfigType } from '../api/actions/updateUserConfig';
import { useEffect, useState } from 'react';
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

  const location = useLocation();

  const currentPageFromUrl = Number(searchParams.get('page'));

  const [currentPage, setCurrentPage] = useState(currentPageFromUrl);

  useEffect(() => {
    setAuth(auth);
    setUserConfig(userConfig);
    setUserAccount(userAccount);
    setAppSettingsConfig(appSettings);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (currentPageFromUrl !== currentPage) {
      setCurrentPage(0);
    }

    // This should only be executed when location.pathname changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  useEffect(() => {
    if (currentPageFromUrl !== currentPage) {
      setCurrentPage(currentPageFromUrl);
    }

    // This should only be executed when currentPageFromUrl changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPageFromUrl]);

  useEffect(() => {
    if (currentPageFromUrl !== currentPage) {
      setSearchParams(params => {
        if (currentPage == 0) {
          params.delete('page');
        } else {
          params.set('page', currentPage.toString());
        }

        return params;
      });
    }

    // This should only be executed when currentPage changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

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
