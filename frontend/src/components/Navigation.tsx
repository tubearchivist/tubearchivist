import { Link, useNavigate } from 'react-router-dom';
import iconSearch from '/img/icon-search.svg';
import iconGear from '/img/icon-gear.svg';
import iconExit from '/img/icon-exit.svg';
import Routes from '../configuration/routes/RouteList';
import NavigationItem from './NavigationItem';
import logOut from '../api/actions/logOut';
import useIsAdmin from '../functions/useIsAdmin';

const Navigation = () => {
  const isAdmin = useIsAdmin();
  const navigate = useNavigate();
  const handleLogout = async (event: { preventDefault: () => void }) => {
    event.preventDefault();
    await logOut();
    navigate(Routes.Login);
  };

  return (
    <div className="boxed-content">
      <Link to={Routes.Home}>
        <div className="top-banner"></div>
      </Link>
      <div className="top-nav">
        <div className="nav-items">
          <NavigationItem label="home" navigateTo={Routes.Home} />
          <NavigationItem label="channels" navigateTo={Routes.Channels} />
          <NavigationItem label="playlists" navigateTo={Routes.Playlists} />

          {isAdmin && <NavigationItem label="downloads" navigateTo={Routes.Downloads} />}
        </div>
        <div className="nav-icons">
          <Link to={Routes.Search}>
            <img src={iconSearch} alt="search-icon" title="Search" />
          </Link>
          <Link to={Routes.SettingsDashboard}>
            <img src={iconGear} alt="gear-icon" title="Settings" />
          </Link>
          <img
            className="alert-hover"
            src={iconExit}
            alt="exit-icon"
            title="Logout"
            onClick={handleLogout}
          />
        </div>
      </div>
    </div>
  );
};

export default Navigation;
