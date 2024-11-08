import { Link, useOutletContext } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { OutletContextType } from '../pages/Base';

const SettingsNavigation = () => {
  const { isAdmin } = useOutletContext() as OutletContextType;

  return (
    <>
      <div className="info-box-item child-page-nav">
        <Link to={Routes.SettingsDashboard}>
          <h3>Dashboard</h3>
        </Link>
        <Link to={Routes.SettingsUser}>
          <h3>User</h3>
        </Link>

        {isAdmin && (
          <>
            <Link to={Routes.SettingsApplication}>
              <h3>Application</h3>
            </Link>
            <Link to={Routes.SettingsScheduling}>
              <h3>Scheduling</h3>
            </Link>
            <Link to={Routes.SettingsActions}>
              <h3>Actions</h3>
            </Link>
          </>
        )}
      </div>
    </>
  );
};

export default SettingsNavigation;
