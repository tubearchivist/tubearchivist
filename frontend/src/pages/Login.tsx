import { useEffect, useState } from 'react';
import Routes from '../configuration/routes/RouteList';
import { useNavigate } from 'react-router-dom';
import Colours from '../configuration/colours/Colours';
import Button from '../components/Button';
import signIn from '../api/actions/signIn';
import loadAuth from '../api/loader/loadAuth';
import LoadingIndicator from '../components/LoadingIndicator';

const Login = () => {
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [saveLogin, setSaveLogin] = useState(false);
  const [waitingForBackend, setWaitingForBackend] = useState(false);
  const [waitedCount, setWaitedCount] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (event: { preventDefault: () => void }) => {
    event.preventDefault();

    if (waitingForBackend) {
      return false;
    }

    setErrorMessage(null);

    const loginResponse = await signIn(username, password, saveLogin);

    const signedIn = loginResponse.status === 204;

    if (signedIn) {
      navigate(Routes.Home);
    } else {
      const data = await loginResponse.json();
      setErrorMessage(data?.error || 'Unknown Error');
      navigate(Routes.Login);
    }
  };

  useEffect(() => {
    let retryCount = 0;

    const backendCheckInterval = setInterval(async () => {
      try {
        const auth = await loadAuth();

        const authData = await auth.json();

        if (auth.status === 403) {
          setWaitingForBackend(false);
          clearInterval(backendCheckInterval);
        }

        if (authData.response === 'pong') {
          setWaitingForBackend(false);
          clearInterval(backendCheckInterval);

          navigate(Routes.Home);
        }
      } catch (error) {
        console.log('Checking backend availability: ', error);
        retryCount += 1;
        setWaitedCount(retryCount);
        setWaitingForBackend(true);
      }
    }, 1000);

    return () => {
      clearInterval(backendCheckInterval);
    };
  }, [navigate]);

  return (
    <>
      <title>TA | Welcome</title>
      <Colours />
      <div className="boxed-content login-page">
        <img alt="tube-archivist-logo" />
        <h1>Tube Archivist</h1>
        <h2>Your Self Hosted YouTube Media Server</h2>

        {errorMessage !== null && (
          <p className="danger-zone">
            Failed to login.
            <br />
            {errorMessage}
          </p>
        )}

        <form onSubmit={handleSubmit}>
          <input
            type="text"
            name="username"
            id="id_username"
            placeholder="Username"
            autoComplete="username"
            maxLength={150}
            required={true}
            value={username}
            onChange={event => setUsername(event.target.value)}
          />

          <br />

          <input
            type="password"
            name="password"
            id="id_password"
            placeholder="Password"
            autoComplete="current-password"
            required={true}
            value={password}
            onChange={event => setPassword(event.target.value)}
          />

          <br />

          <p>
            Remember me:{' '}
            <input
              type="checkbox"
              name="remember_me"
              id="id_remember_me"
              checked={saveLogin}
              onChange={() => {
                setSaveLogin(!saveLogin);
              }}
            />
          </p>

          <input type="hidden" name="next" value={Routes.Home} />

          {waitingForBackend && (
            <>
              <p>
                Waiting for backend <LoadingIndicator />
              </p>
            </>
          )}

          {!waitingForBackend && <Button label="Login" type="submit" />}
        </form>

        {waitedCount > 10 && (
          <div className="info-box">
            <div className="info-box-item">
              <h2>Having issues?</h2>

              <div className="help-text left-align">
                <p>Please verify that you setup your environment correctly:</p>
                <ul>
                  <li
                    onClick={() => {
                      navigator.clipboard.writeText(`TA_HOST=${window.location.origin}`);
                    }}
                  >
                    TA_HOST={window.location.origin}
                  </li>
                  <li
                    onClick={() => {
                      navigator.clipboard.writeText('REDIS_CON=redis://archivist-redis:6379');
                    }}
                  >
                    REDIS_CON=redis://archivist-redis:6379
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        <p className="login-links">
          <span>
            <a href="https://github.com/tubearchivist/tubearchivist" target="_blank">
              Github
            </a>
          </span>{' '}
          <span>
            <a href="https://github.com/tubearchivist/tubearchivist#donate" target="_blank">
              Donate
            </a>
          </span>
        </p>
      </div>
      <div className="footer-colors">
        <div className="col-1"></div>
        <div className="col-2"></div>
        <div className="col-3"></div>
      </div>
    </>
  );
};

export default Login;
