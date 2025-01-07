import defaultHeaders from '../configuration/defaultHeaders';
import getApiUrl from '../configuration/getApiUrl';
import getFetchCredentials from '../configuration/getFetchCredentials';
import logOut from '../api/actions/logOut';
import getCookie from './getCookie';

export interface ApiClientOptions extends Omit<RequestInit, 'body'> {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: Record<string, unknown> | string;
}

const APIClient = async (
  endpoint: string,
  { method = 'GET', body, headers = {}, ...options }: ApiClientOptions = {},
) => {
  const apiUrl = getApiUrl();
  const csrfToken = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}${endpoint}`, {
    method,
    headers: {
      ...defaultHeaders,
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      ...headers,
    },
    credentials: getFetchCredentials(),
    body: body ? JSON.stringify(body) : undefined,
    ...options,
  });

  // Handle common errors
  if (response.status === 401) {
    logOut();
    window.location.href = '/login';
    throw new Error('Unauthorized: Redirecting to login.');
  }

  if (response.status === 403) {
    logOut();
    window.location.href = '/login';
    throw new Error('Forbidden: Access denied.');
  }

  // Try parsing response data
  let data;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
    console.error(`error fetching data: ${error}`);
  }

  if (!response.ok) {
    throw new Error(data?.detail || 'An error occurred while processing the request.');
  }

  return data;
};

export default APIClient;
