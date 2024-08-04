import isDevEnvironment from '../functions/isDevEnvironment';

const getFetchCredentials = () => {
  const isDevEnv = isDevEnvironment();

  return isDevEnv ? 'include' : 'same-origin';
};

export default getFetchCredentials;
