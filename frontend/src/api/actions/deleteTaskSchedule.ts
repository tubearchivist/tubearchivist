import APIClient from '../../functions/APIClient';
import { TaskScheduleNameType } from './createTaskSchedule';

const deleteTaskSchedule = async (taskName: TaskScheduleNameType) => {
  return APIClient(`/api/task/schedule/${taskName}/`, {
    method: 'DELETE',
  });
};

export default deleteTaskSchedule;
