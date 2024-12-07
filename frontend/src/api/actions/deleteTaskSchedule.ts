import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import getCookie from '../../functions/getCookie';
import isDevEnvironment from '../../functions/isDevEnvironment';
import { TaskScheduleNameType } from './createTaskSchedule';

const deleteTaskSchedule = async (taskName: TaskScheduleNameType) => {
  const apiUrl = getApiUrl();
  const csrfCookie = getCookie('csrftoken');

  const response = await fetch(`${apiUrl}/api/task/schedule/${taskName}/`, {
    method: 'DELETE',
    headers: {
      ...defaultHeaders,
      'X-CSRFToken': csrfCookie || '',
    },
    credentials: getFetchCredentials(),
  });

  const scheduledTask = await response.json();

  if (isDevEnvironment()) {
    console.log('deleteTaskSchedule', scheduledTask);
  }

  return scheduledTask;
};

export default deleteTaskSchedule;
