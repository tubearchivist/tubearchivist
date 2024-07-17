import { Link } from 'react-router-dom';
import iconSearch from '/img/icon-search.svg';
import iconGear from '/img/icon-gear.svg';
import iconExit from '/img/icon-exit.svg';
import Routes from '../configuration/routes/RouteList';
import NavigationItem from './NavigationItem';

interface NavigationProps {
  isAdmin: boolean;
}

const Navigation = ({ isAdmin }: NavigationProps) => {
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
          <Link to={Routes.Logout}>
            <img className="alert-hover" src={iconExit} alt="exit-icon" title="Logout" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Navigation;
