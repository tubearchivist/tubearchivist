import APIClient from '../../functions/APIClient';
import { AppSettingsConfigType } from '../loader/loadAppsettingsConfig';

const updateAppsettingsConfig = async (updatedConfig: Partial<AppSettingsConfigType>) => {
  return APIClient('/api/appsettings/config/', {
    method: 'POST',
    body: updatedConfig,
  });
};

export default updateAppsettingsConfig;
