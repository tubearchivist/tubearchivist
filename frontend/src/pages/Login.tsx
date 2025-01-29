import { useState } from 'react';
import Routes from '../configuration/routes/RouteList';
import { useNavigate } from 'react-router-dom';
import useColours from '../configuration/colours/useColours';
import Button from '../components/Button';
import signIn from '../api/actions/signIn';

const Login = () => {
  useColours();

  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [saveLogin, setSaveLogin] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (event: { preventDefault: () => void }) => {
    event.preventDefault();

    setErrorMessage(null);

    const loginResponse = await signIn(username, password, saveLogin);

    const signedIn = loginResponse.status === 200;

    if (signedIn) {
      navigate(Routes.Home);
    } else {
      const data = await loginResponse.json();
      setErrorMessage(data?.message || 'Unknown Error');
      navigate(Routes.Login);
    }
  };

  return (
    <>
      <title>TA | Welcome</title>
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

          <Button label="Login" type="submit" />
        </form>
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
