import { useNavigate } from 'react-router-dom';
import updateUserConfig, { ColourVariants, UserConfigType } from '../api/actions/updateUserConfig';
import { ColourConstant } from '../configuration/colours/useColours';
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
  const navigate = useNavigate();

  const [styleSheet, setStyleSheet] = useState<ColourVariants>(userConfig.stylesheet);
  const [styleSheetRefresh, setStyleSheetRefresh] = useState(false);
  const [pageSize, setPageSize] = useState<number>(userConfig.page_size);
  const [showHelpText, setShowHelpText] = useState(userConfig.show_help_text);

  useEffect(() => {
    (async () => {
      setStyleSheet(userConfig.stylesheet);
      setPageSize(userConfig.page_size);
      setShowHelpText(userConfig.show_help_text);
    })();
  }, [userConfig.page_size, userConfig.stylesheet, userConfig.show_help_text]);

  const handleStyleSheetChange = async (selectedStyleSheet: ColourVariants) => {
    handleUserConfigUpdate({ stylesheet: selectedStyleSheet });
    setStyleSheet(selectedStyleSheet);
    setStyleSheetRefresh(true);
  };

  const handlePageSizeChange = async () => {
    handleUserConfigUpdate({ page_size: pageSize });
  };

  const handleShowHelpTextChange = async (configKey: string, configValue: boolean) => {
    handleUserConfigUpdate({ [configKey]: configValue });
  };

  const handleUserConfigUpdate = async (config: Partial<UserConfigType>) => {
    const updatedUserConfig = await updateUserConfig(config);
    setUserConfig(updatedUserConfig);
  };

  const handlePageRefresh = () => {
    navigate(0);
    setStyleSheetRefresh(false);
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
                {styleSheetRefresh && <button onClick={handlePageRefresh}>Refresh</button>}
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
