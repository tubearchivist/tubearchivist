import APIClient from '../../functions/APIClient';

const loadSearch = async (query: string) => {
  return APIClient(`/api/search/?query=${query}`);
};

export default loadSearch;
