import { Outlet, useLoaderData, useLocation, useSearchParams } from 'react-router-dom';
import Footer, { TaUpdateType } from '../components/Footer';
import importColours from '../configuration/colours/getColours';
import { UserMeType } from '../api/actions/updateUserConfig';
import { useEffect, useState } from 'react';
import Navigation from '../components/Navigation';
import loadIsAdmin from '../functions/getIsAdmin';

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
  isAdmin: boolean;
  currentPage: number;
  setCurrentPage: (page: number) => void;
};

const Base = () => {
  const { userConfig, auth } = useLoaderData() as BaseLoaderData;
  const location = useLocation();

  const userMeConfig = userConfig.config;

  const searchParams = new URLSearchParams(location.search);

  const currentPageFromUrl = Number(searchParams.get('page'));

  const [currentPage, setCurrentPage] = useState(currentPageFromUrl);
  const [, setSearchParams] = useSearchParams();

  const isAdmin = loadIsAdmin(userConfig);
  const version = auth.version;
  const taUpdate = auth.ta_update;

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

  importColours(userMeConfig.stylesheet);

  return (
    <>
      <div className="main-content">
        <Navigation isAdmin={isAdmin} />
        {/** Outlet: https://reactrouter.com/en/main/components/outlet */}
        <Outlet context={{ isAdmin, currentPage, setCurrentPage }} />
      </div>
      <Footer version={version} taUpdate={taUpdate} />
    </>
  );
};

export default Base;
