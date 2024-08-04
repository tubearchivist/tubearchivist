import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import isDevEnvironment from '../../functions/isDevEnvironment';

const loadSearch = async (query: string) => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/search/?query=${query}`, {
    headers: defaultHeaders,
  });

  const searchResults = await response.json();

  if (isDevEnvironment()) {
    console.log('loadSearch', searchResults);
  }

  return searchResults;
};

export default loadSearch;
