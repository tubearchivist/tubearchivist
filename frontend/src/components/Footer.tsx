import { Link } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { useAuthStore } from '../stores/AuthDataStore';

const Footer = () => {
  const currentYear = new Date().getFullYear();
  const { auth } = useAuthStore();
  const version = auth?.version;
  const taUpdate = auth?.ta_update;

  return (
    <div className="footer">
      <div className="boxed-content">
        <span>© 2021 - {currentYear} </span>
        <span>TubeArchivist </span>
        <span>{version} </span>
        {taUpdate?.version && (
          <>
            <span className="danger-zone">
              {taUpdate.version} available
              {taUpdate.is_breaking && <span className="danger-zone">Breaking Changes!</span>}
            </span>{' '}
            <span>
              <a
                href={`https://github.com/tubearchivist/tubearchivist/releases/tag/${taUpdate.version}`}
                target="_blank"
              >
                Release Page
              </a>{' '}
              |{' '}
            </span>
          </>
        )}
        <span>
          <Link to={Routes.About}>About</Link> |{' '}
          <a href="https://github.com/tubearchivist/tubearchivist" target="_blank">
            GitHub
          </a>{' '}
          |{' '}
          <a href="https://hub.docker.com/r/bbilly1/tubearchivist" target="_blank">
            Docker Hub
          </a>{' '}
          |{' '}
          <a href="https://www.tubearchivist.com/discord" target="_blank">
            Discord
          </a>{' '}
          | <a href="https://www.reddit.com/r/TubeArchivist/">Reddit</a>
        </span>
      </div>
    </div>
  );
};

export default Footer;
