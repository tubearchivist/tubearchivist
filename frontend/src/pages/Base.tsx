import { Outlet, useLoaderData, useLocation, useSearchParams } from 'react-router-dom';
import Footer from '../components/Footer';
import useColours from '../configuration/colours/useColours';
import { UserMeType } from '../api/actions/updateUserConfig';
import { useEffect, useState } from 'react';
import Navigation from '../components/Navigation';
import { useAuthStore } from '../stores/AuthDataStore';
import { useUserConfigStore } from '../stores/UserConfigStore';

export type TaUpdateType = {
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
  userConfig: UserMeType;
  auth: AuthenticationType;
};

export type OutletContextType = {
  currentPage: number;
  setCurrentPage: (page: number) => void;
};

const Base = () => {
  const { setAuth } = useAuthStore();
  const { setUserConfig } = useUserConfigStore();
  const { userConfig, auth } = useLoaderData() as BaseLoaderData;

  const location = useLocation();

  const searchParams = new URLSearchParams(location.search);

  const currentPageFromUrl = Number(searchParams.get('page'));

  const [currentPage, setCurrentPage] = useState(currentPageFromUrl);
  const [, setSearchParams] = useSearchParams();

  useEffect(() => {
    setAuth(auth);
    setUserConfig(userConfig);
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
        params.set('page', currentPage.toString());

        return params;
      });
    }

    // This should only be executed when currentPage changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage]);

  useColours();

  return (
    <>
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
