import defaultHeaders from '../configuration/defaultHeaders';
import getApiUrl from '../configuration/getApiUrl';
import getFetchCredentials from '../configuration/getFetchCredentials';
import logOut from '../api/actions/logOut';
import getCookie from './getCookie';
import Routes from '../configuration/routes/RouteList';
import { useBackendStore } from '../stores/BackendStore';

export interface ApiClientOptions extends Omit<RequestInit, 'body'> {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: Record<string, unknown> | string;
}

export interface ApiError {
  status: number;
  message: string;
}

export type ResponseErrorType = {
  error: string;
};

export type ApiResponseType<T> = {
  data?: T;
  error?: ResponseErrorType;
  status: number;
};

const APIClient = async <T>(
  endpoint: string,
  { method = 'GET', body, headers = {}, ...options }: ApiClientOptions = {},
): Promise<ApiResponseType<T>> => {
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

  const backendTimestamp = response.headers.get('X-Start-Timestamp');
  if (backendTimestamp) {
    const { setStartTimestamp } = useBackendStore.getState();
    setStartTimestamp(backendTimestamp);
  }

  // Handle common errors
  if (response.status === 400) {
    const data = await response.json();
    throw {
      status: response.status,
      message: data?.message || data?.error || 'An error occurred while processing the request.',
    } as ApiError;
  }

  if (response.status === 401) {
    logOut();
    window.location.href = Routes.Login;
    throw new Error('Unauthorized: Redirecting to login.');
  }

  if (response.status === 403) {
    logOut();
    window.location.href = Routes.Login;
    throw new Error('Forbidden: Access denied.');
  }

  // expected empty response
  if (response.status === 204) {
    return {
      data: undefined,
      error: undefined,
      status: response.status,
    };
  }

  // Try parsing response data
  try {
    const responseJson = await response.json();

    const hasErrorMessage = responseJson.error;

    return {
      data: !hasErrorMessage ? responseJson : undefined,
      error: hasErrorMessage ? responseJson : undefined,
      status: response.status,
    };
  } catch (error) {
    console.error(`error fetching data: ${error}`);

    return {
      data: undefined,
      error: {
        error: `error fetching data: ${error}`,
      },
      status: response.status,
    };
  }
};

export default APIClient;
