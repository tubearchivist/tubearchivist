import defaultHeaders from '../../configuration/defaultHeaders';
import getApiUrl from '../../configuration/getApiUrl';
import getFetchCredentials from '../../configuration/getFetchCredentials';
import isDevEnvironment from '../../functions/isDevEnvironment';

type ScheduleType = {
  name: string;
  schedule: string;
  schedule_human: string;
  last_run_at: string;
  config: {
    days?: number;
    rotate?: number;
  };
};

export type ScheduleResponseType = ScheduleType[];

const loadSchedule = async (): Promise<ScheduleResponseType> => {
  const apiUrl = getApiUrl();

  const response = await fetch(`${apiUrl}/api/task/schedule/`, {
    headers: defaultHeaders,
    credentials: getFetchCredentials(),
  });

  const schedule = await response.json();

  if (isDevEnvironment()) {
    console.log('loadSchedule', schedule);
  }

  return schedule;
};

export default loadSchedule;
