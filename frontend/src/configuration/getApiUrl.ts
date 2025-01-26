const DEV_API_URL = 'http://localhost:8000';
const PROD_API_URL = window.location.origin;

const getApiUrl = () => {
  let url = PROD_API_URL;

  if (import.meta.env.DEV) {
    url = DEV_API_URL;
  }

  return url;
};

export default getApiUrl;
