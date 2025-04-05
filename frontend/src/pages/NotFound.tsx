import { Link } from 'react-router-dom';
import Colours from '../configuration/colours/Colours';
import Routes from '../configuration/routes/RouteList';

const NotFound = ({ failType = 'page' }) => {
  return (
    <>
      <title>404 | Not found</title>
      <Colours />
      <div id="error-page" style={{ margin: '10%' }}>
        <h1>Oops!</h1>
        <p>
          <i>404</i>
          <span>: That {failType} does not exist.</span>
        </p>
        <Link to={Routes.Home}>Go Home</Link>
      </div>
    </>
  );
};

export default NotFound;
