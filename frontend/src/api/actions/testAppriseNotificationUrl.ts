import APIClient from '../../functions/APIClient';
import { AppriseTaskNameType } from './createAppriseNotificationUrl';

export type TestNotificationResponseType = {
  success: boolean;
  message: string;
};

const testAppriseNotificationUrl = async (taskName: AppriseTaskNameType, url: string) => {
  return APIClient<TestNotificationResponseType>('/api/task/notification/test/', {
    method: 'POST',
    body: { task_name: taskName, url },
  });
};

export default testAppriseNotificationUrl;
