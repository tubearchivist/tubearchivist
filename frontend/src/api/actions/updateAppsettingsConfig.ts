import APIClient from '../../functions/APIClient';

const updateAppsettingsConfig = async (
  configKey: string,
  configValue: string | boolean | number | null,
) => {
  return APIClient('/api/appsettings/config/', {
    method: 'POST',
    body: { [configKey]: configValue },
  });
};

export default updateAppsettingsConfig;
