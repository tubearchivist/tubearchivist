import getApiUrl from '../../configuration/getApiUrl';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadSearch = async (query: string) => {
  const apiUrl = getApiUrl();
  const headers = new Headers();

  const csrfCookie = getCookie('csrftoken');
  if (csrfCookie) {
    headers.append('X-CSRFToken', csrfCookie);
  }

  const response = await fetch(`${apiUrl}/api/search/?query=${query}`, {
    headers,
  });

  const searchResults = await response.json();

  if (isDevEnvironment()) {
    console.log('loadSearch', searchResults);
  }

  return searchResults;
};

export default loadSearch;
