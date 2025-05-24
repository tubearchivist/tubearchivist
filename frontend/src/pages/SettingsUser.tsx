import updateUserConfig, {
  ColourConstant,
  ColourVariants,
  FileSizeUnits,
  UserConfigType,
} from '../api/actions/updateUserConfig';
import SettingsNavigation from '../components/SettingsNavigation';
import Notifications from '../components/Notifications';
import Button from '../components/Button';
import useIsAdmin from '../functions/useIsAdmin';
import { useUserConfigStore } from '../stores/UserConfigStore';
import { useEffect, useState } from 'react';
import ToggleConfig from '../components/ToggleConfig';

const SettingsUser = () => {
  const { userConfig, setUserConfig } = useUserConfigStore();
  const isAdmin = useIsAdmin();

  const [styleSheet, setStyleSheet] = useState<ColourVariants>(userConfig.stylesheet);
  const [pageSize, setPageSize] = useState<number>(userConfig.page_size);
  const [showHelpText, setShowHelpText] = useState(userConfig.show_help_text);
  const [selectedFileSizeUnit, setSelectedFileSizeUnit] = useState(FileSizeUnits.Binary);

  useEffect(() => {
    (async () => {
      setStyleSheet(userConfig.stylesheet);
      setPageSize(userConfig.page_size);
      setShowHelpText(userConfig.show_help_text);
      setSelectedFileSizeUnit(userConfig.file_size_unit);
    })();
  }, [
    userConfig.page_size,
    userConfig.stylesheet,
    userConfig.show_help_text,
    userConfig.file_size_unit,
  ]);

  const handleStyleSheetChange = async (selectedStyleSheet: ColourVariants) => {
    handleUserConfigUpdate({ stylesheet: selectedStyleSheet });
    setStyleSheet(selectedStyleSheet);

    // Store in local storage for pages like login, without a userConfig
    localStorage.setItem('stylesheet', selectedStyleSheet);
  };

  const handlePageSizeChange = async () => {
    handleUserConfigUpdate({ page_size: pageSize });
  };

  const handleShowHelpTextChange = async (configKey: string, configValue: boolean) => {
    handleUserConfigUpdate({ [configKey]: configValue });
  };

  const handleFileSizeUnitChange = async (configKey: string, configValue: string) => {
    handleUserConfigUpdate({ [configKey]: configValue });
  };

  const handleUserConfigUpdate = async (config: Partial<UserConfigType>) => {
    const updatedUserConfig = await updateUserConfig(config);
    const { data: updatedUserConfigData } = updatedUserConfig;

    if (updatedUserConfigData) {
      setUserConfig(updatedUserConfigData);
    }
  };

  return (
    <>
      <title>TA | User Settings</title>
      <div className="boxed-content">
        <SettingsNavigation />
        <Notifications pageName={'all'} />

        <div className="title-bar">
          <h1>User Configurations</h1>
        </div>
        <div className="info-box">
          <div className="info-box-item">
            <h2>Customize user Interface</h2>
            <div className="settings-box-wrapper">
              <div>
                <p>Switch your color scheme</p>
              </div>
              <div>
                <select
                  name="stylesheet"
                  id="id_stylesheet"
                  value={styleSheet}
                  onChange={event => {
                    handleStyleSheetChange(event.target.value as ColourVariants);
                  }}
                >
                  {Object.entries(ColourConstant).map(([key, value]) => {
                    return (
                      <option key={key} value={value}>
                        {key}
                      </option>
                    );
                  })}
                </select>
              </div>
            </div>

            <div className="settings-box-wrapper">
              <div>
                <p>Archive view page size</p>
              </div>
              <div>
                <input
                  type="number"
                  name="page_size"
                  id="id_page_size"
                  value={pageSize || 12}
                  onChange={event => {
                    setPageSize(Number(event.target.value));
                  }}
                />

                <div className="button-box">
                  {userConfig.page_size !== pageSize && (
                    <>
                      <button onClick={handlePageSizeChange}>Update</button>
                      <button onClick={() => setPageSize(userConfig.page_size)}>Cancel</button>
                    </>
                  )}
                </div>
              </div>
            </div>

            <div className="settings-box-wrapper">
              <div>
                <p>Show help text</p>
              </div>

              <ToggleConfig
                name="show_help_text"
                value={showHelpText}
                updateCallback={handleShowHelpTextChange}
              />
            </div>

            <div
              className="settings-box-wrapper"
              title="Metric (SI) units, aka powers of 1000. Binary (IEC), aka powers of 1024."
            >
              <div>
                <p>File size units:</p>
              </div>

              <select
                value={selectedFileSizeUnit}
                onChange={event => {
                  handleFileSizeUnitChange('file_size_unit', event.currentTarget.value);
                }}
              >
                <option value={FileSizeUnits.Metric}>SI units</option>
                <option value={FileSizeUnits.Binary}>Binary units</option>
              </select>
            </div>
          </div>
        </div>

        {isAdmin && (
          <>
            <div className="settings-group">
              <h2>User Management</h2>
              <p>
                Access the admin interface for basic user management functionality like adding and
                deleting users, changing passwords and more.
              </p>
              <a href="/admin/">
                <Button label="Admin Interface" />
              </a>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default SettingsUser;
