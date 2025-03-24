import APIClient from '../../functions/APIClient';

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

const loadSchedule = async () => {
  return APIClient<ScheduleResponseType>('/api/task/schedule/');
};

export default loadSchedule;
