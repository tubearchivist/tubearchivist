import APIClient from '../../functions/APIClient';

const stopTaskByName = async (taskId: string) => {
  APIClient(`/api/task/by-id/${taskId}/`, {
    method: 'POST',
    body: { command: 'stop' },
  });
};

export default stopTaskByName;
