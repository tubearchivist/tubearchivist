import { useEffect, useState } from 'react';
import loadSnapshots from '../api/loader/loadSnapshots';
import Notifications from '../components/Notifications';
import PaginationDummy from '../components/PaginationDummy';
import SettingsNavigation from '../components/SettingsNavigation';
import restoreSnapshot from '../api/actions/restoreSnapshot';
import queueSnapshot from '../api/actions/queueSnapshot';
// import updateCookie, { ValidatedCookieType } from '../api/actions/updateCookie';
import deleteApiToken from '../api/actions/deleteApiToken';
import Button from '../components/Button';
import loadAppsettingsConfig, { AppSettingsConfigType } from '../api/loader/loadAppsettingsConfig';
import updateAppsettingsConfig from '../api/actions/updateAppsettingsConfig';
import loadApiToken from '../api/loader/loadApiToken';
import InputConfig from '../components/InputConfig';
import ToggleConfig from '../components/ToggleConfig';
import updateCookie from '../api/actions/updateCookie';
import loadCookie, { CookieStateType } from '../api/loader/loadCookie';
import deleteCookie from '../api/actions/deleteCookie';
import validateCookie from '../api/actions/validateCookie';

type SnapshotType = {
  id: string;
  state: string;
  es_version: string;
  start_date: string;
  end_date: string;
  end_stamp: number;
  duration_s: number;
};

type SnapshotListType = {
  next_exec: number;
  next_exec_str: string;
  expire_after: string;
  snapshots?: SnapshotType[];
};

type SettingsApplicationReponses = {
  snapshots?: SnapshotListType;
  appSettingsConfig?: AppSettingsConfigType;
  apiToken?: string;
  cookieState: CookieStateType;
};

const SettingsApplication = () => {
  const [response, setResponse] = useState<SettingsApplicationReponses>();
  const [refresh, setRefresh] = useState(false);

  const snapshots = response?.snapshots;
  const appSettingsConfig = response?.appSettingsConfig;
  const apiToken = response?.apiToken;

  // Subscriptions
  const [videoPageSize, setVideoPageSize] = useState<number | null>(null);
  const [livePageSize, setLivePageSize] = useState<number | null>(null);
  const [shortPageSize, setShortPageSize] = useState<number | null>(null);
  const [isAutostart, setIsAutostart] = useState<boolean>(false);

  // Downloads
  const [currentDownloadSpeed, setCurrentDownloadSpeed] = useState<number | null>(null);
  const [currentThrottledRate, setCurrentThrottledRate] = useState<number | null>(null);
  const [currentScrapingSleep, setCurrentScrapingSleep] = useState<number | null>(null);
  const [currentAutodelete, setCurrentAutodelete] = useState<number | null>(null);

  // Download Format
  const [downloadsFormat, setDownloadsFormat] = useState<string | null>(null);
  const [downloadsFormatSort, setDownloadsFormatSort] = useState<string | null>(null);
  const [downloadsExtractorLang, setDownloadsExtractorLang] = useState<string | null>(null);
  const [embedMetadata, setEmbedMetadata] = useState(false);
  const [embedThumbnail, setEmbedThumbnail] = useState(false);

  // Subtitles
  const [subtitleLang, setSubtitleLang] = useState<string | null>(null);
  const [subtitleSource, setSubtitleSource] = useState<string | null>(null);
  const [indexSubtitles, setIndexSubtitles] = useState(false);

  // Comments
  const [commentsMax, setCommentsMax] = useState<string | null>(null);
  const [commentsSort, setCommentsSort] = useState<string>('');

  // Cookie
  const [cookieFormData, setCookieFormData] = useState<string>('');
  const [showCookieForm, setShowCookieForm] = useState<boolean>(false);
  // const [cookieImport, setCookieImport] = useState(false);
  // const [validatingCookie, setValidatingCookie] = useState(false);
  // const [cookieResponse, setCookieResponse] = useState<ValidatedCookieType>();

  // Integrations
  const [showApiToken, setShowApiToken] = useState(false);
  const [downloadDislikes, setDownloadDislikes] = useState(false);
  const [enableSponsorBlock, setEnableSponsorBlock] = useState(false);

  // Snapshots
  const [enableSnapshots, setEnableSnapshots] = useState(false);
  const [isSnapshotQueued, setIsSnapshotQueued] = useState(false);
  const [restoringSnapshot, setRestoringSnapshot] = useState(false);

  const fetchData = async () => {
    const snapshotResponse = await loadSnapshots();
    const appSettingsConfig = await loadAppsettingsConfig();
    const apiToken = await loadApiToken();
    const cookieState = await loadCookie();

    // Subscriptions
    setVideoPageSize(appSettingsConfig.subscriptions.channel_size);
    setLivePageSize(appSettingsConfig.subscriptions.live_channel_size);
    setShortPageSize(appSettingsConfig.subscriptions.shorts_channel_size);
    setIsAutostart(appSettingsConfig.subscriptions.auto_start);

    // Downloads
    setCurrentDownloadSpeed(appSettingsConfig.downloads.limit_speed);
    setCurrentThrottledRate(appSettingsConfig.downloads.throttledratelimit);
    setCurrentScrapingSleep(appSettingsConfig.downloads.sleep_interval);
    setCurrentAutodelete(appSettingsConfig.downloads.autodelete_days);

    // Download Format
    setDownloadsFormat(appSettingsConfig.downloads.format);
    setDownloadsFormatSort(appSettingsConfig.downloads.format_sort);
    setDownloadsExtractorLang(appSettingsConfig.downloads.extractor_lang);
    setEmbedMetadata(appSettingsConfig.downloads.add_metadata);
    setEmbedThumbnail(appSettingsConfig.downloads.add_thumbnail);

    // Subtitles
    setSubtitleLang(appSettingsConfig.downloads.subtitle);
    setSubtitleSource(appSettingsConfig.downloads.subtitle_source);
    setIndexSubtitles(appSettingsConfig.downloads.subtitle_index);

    // Comments
    setCommentsMax(appSettingsConfig.downloads.comment_max);
    setCommentsSort(appSettingsConfig.downloads.comment_sort);

    // Cookie
    // setCookieImport(appSettingsConfig?.downloads.cookie_import);

    // Integrations
    setDownloadDislikes(appSettingsConfig.downloads.integrate_ryd);
    setEnableSponsorBlock(appSettingsConfig.downloads.integrate_sponsorblock);

    // Snapshots
    setEnableSnapshots(appSettingsConfig.application.enable_snapshot);

    setResponse({
      snapshots: snapshotResponse,
      appSettingsConfig,
      apiToken: apiToken.token,
      cookieState,
    });
  };

  const handleUpdateConfig = async (
    configKey: string,
    configValue: string | boolean | number | null,
  ) => {
    await updateAppsettingsConfig(configKey, configValue);
    setRefresh(true);
  };

  const handleCookieUpdate = async () => {
    await updateCookie(cookieFormData);
    setCookieFormData('');
    setShowCookieForm(false);
    setRefresh(true);
  };

  const handleCookieRevoke = async () => {
    await deleteCookie();
    setRefresh(true);
  };

  const handleCookieValidate = async () => {
    await validateCookie();
    setRefresh(true);
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (refresh) {
      fetchData();
      setRefresh(false);
    }
  }, [refresh]);

  return (
    <>
      <title>TA | Application Settings</title>
      <div className="boxed-content">
        <SettingsNavigation />
        <Notifications pageName={'all'} />

        <div className="title-bar">
          <h1>Application Configurations</h1>
        </div>
        {appSettingsConfig && (
          <div className="info-box">
            <div className="info-box-item">
              <h2 id="subscriptions">Subscriptions</h2>
              <p>Disable shorts or streams by setting their page size to 0 (zero).</p>
              <div className="settings-box-wrapper">
                <div>
                  <p>Videos page size</p>
                </div>
                <InputConfig
                  type="number"
                  name="subscriptions.channel_size"
                  value={videoPageSize}
                  setValue={setVideoPageSize}
                  oldValue={appSettingsConfig?.subscriptions.channel_size}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Live Streams page size</p>
                </div>
                <InputConfig
                  type="number"
                  name="subscriptions.live_channel_size"
                  value={livePageSize}
                  setValue={setLivePageSize}
                  oldValue={appSettingsConfig?.subscriptions.live_channel_size}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Shorts page size</p>
                </div>
                <InputConfig
                  type="number"
                  name="subscriptions.shorts_channel_size"
                  value={shortPageSize}
                  setValue={setShortPageSize}
                  oldValue={appSettingsConfig?.subscriptions.shorts_channel_size}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Autostart download subscriptions</p>
                </div>
                <ToggleConfig
                  name="subscriptions.auto_start"
                  value={isAutostart}
                  updateCallback={handleUpdateConfig}
                />
              </div>
            </div>
            <div className="info-box-item">
              <h2 id="downloads">Downloads</h2>
              <div className="settings-box-wrapper">
                <div>
                  <p>Download Speed limit</p>
                </div>
                <InputConfig
                  type="number"
                  name="downloads.limit_speed"
                  value={currentDownloadSpeed}
                  setValue={setCurrentDownloadSpeed}
                  oldValue={appSettingsConfig.downloads.limit_speed}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Throttled rate limit</p>
                </div>
                <InputConfig
                  type="number"
                  name="downloads.throttledratelimit"
                  value={currentThrottledRate}
                  setValue={setCurrentThrottledRate}
                  oldValue={appSettingsConfig.downloads.throttledratelimit}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Sleep interval</p>
                </div>
                <InputConfig
                  type="number"
                  name="downloads.sleep_interval"
                  value={currentScrapingSleep}
                  setValue={setCurrentScrapingSleep}
                  oldValue={appSettingsConfig?.downloads.sleep_interval}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Auto delete watched videos after x days</p>
                </div>
                <InputConfig
                  type="number"
                  name="downloads.autodelete_days"
                  value={currentAutodelete}
                  setValue={setCurrentAutodelete}
                  oldValue={appSettingsConfig?.downloads.autodelete_days}
                  updateCallback={handleUpdateConfig}
                />
              </div>
            </div>
            <div className="info-box-item">
              <h2 id="format">Download Format</h2>
              <div className="settings-box-wrapper">
                <div>
                  <p>Limit video and audio quality format</p>
                </div>
                <InputConfig
                  type="text"
                  name="downloads.format"
                  value={downloadsFormat}
                  setValue={setDownloadsFormat}
                  oldValue={appSettingsConfig.downloads.format}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Sort download formats</p>
                </div>
                <InputConfig
                  type="text"
                  name="downloads.format_sort"
                  value={downloadsFormatSort}
                  setValue={setDownloadsFormatSort}
                  oldValue={appSettingsConfig.downloads.format_sort}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Extractor Language</p>
                </div>
                <InputConfig
                  type="text"
                  name="downloads.extractor_lang"
                  value={downloadsExtractorLang}
                  setValue={setDownloadsExtractorLang}
                  oldValue={appSettingsConfig.downloads.extractor_lang}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Embed metadata</p>
                </div>
                <ToggleConfig
                  name="downloads.add_metadata"
                  value={embedMetadata}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Embed Thumbnail</p>
                </div>
                <ToggleConfig
                  name="downloads.add_thumbnail"
                  value={embedThumbnail}
                  updateCallback={handleUpdateConfig}
                />
              </div>
            </div>
            <div className="info-box-item">
              <h2 id="subtitles">Subtitles</h2>
              <div className="settings-box-wrapper">
                <div>
                  <p>Choose subtitle language</p>
                </div>
                <InputConfig
                  type="text"
                  name="downloads.subtitle"
                  value={subtitleLang}
                  setValue={setSubtitleLang}
                  oldValue={appSettingsConfig?.downloads.subtitle}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              {appSettingsConfig?.downloads.subtitle && (
                <>
                  <div className="settings-box-wrapper">
                    <div>
                      <p>Enable auto generated subtitles</p>
                    </div>
                    <div className="toggle">
                      <div className="toggleBox">
                        <input
                          name="subtitle_source"
                          type="checkbox"
                          checked={subtitleSource === 'auto'}
                          onChange={event => {
                            handleUpdateConfig(
                              'downloads.subtitle_source',
                              event.target.checked ? 'auto' : 'user',
                            );
                          }}
                        />
                        {subtitleSource === 'user' && (
                          <label htmlFor="" className="ofbtn">
                            Off
                          </label>
                        )}
                        {subtitleSource === 'auto' && (
                          <label htmlFor="" className="onbtn">
                            On
                          </label>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="settings-box-wrapper">
                    <div>
                      <p>Enable subtitle index</p>
                    </div>
                    <ToggleConfig
                      name="downloads.subtitle_index"
                      value={indexSubtitles}
                      updateCallback={handleUpdateConfig}
                    />
                  </div>
                </>
              )}
            </div>
            <div className="info-box-item">
              <h2 id="comments">Comments</h2>
              <div className="settings-box-wrapper">
                <div>
                  <p>Index comments</p>
                </div>
                <InputConfig
                  type="text"
                  name="downloads.comment_max"
                  value={commentsMax}
                  setValue={setCommentsMax}
                  oldValue={appSettingsConfig?.downloads.comment_max}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              {appSettingsConfig?.downloads.comment_max && (
                <div className="settings-box-wrapper">
                  <div>
                    <p>Comment sort method</p>
                  </div>
                  <div>
                    <select
                      name="downloads.comment_sort"
                      value={commentsSort}
                      onChange={event => {
                        handleUpdateConfig('downloads.comment_sort', event.target.value);
                      }}
                    >
                      <option value="top">sort comments by top</option>
                      <option value="new">sort comments by new</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
            <div className="info-box-item">
              <h2 id="cookie">Cookie</h2>
              <div className="settings-box-wrapper">
                <div>
                  <p>Use your cookie for yt-dlp</p>
                </div>
                <div>
                  {response?.cookieState?.cookie_enabled ? (
                    <>
                      <p>
                        Cookie enabled. Last validation:{' '}
                        <span className="settings-current">
                          {response.cookieState.validated_str}
                        </span>
                        .
                      </p>
                      <div className="button-box">
                        <button className="danger-button" onClick={handleCookieRevoke}>
                          Revoke
                        </button>
                        <button onClick={handleCookieValidate}>Validate</button>
                      </div>
                    </>
                  ) : (
                    <p>Cookie disabled</p>
                  )}
                  {showCookieForm ? (
                    <>
                      <textarea
                        value={cookieFormData}
                        onChange={e => {
                          setCookieFormData(e.currentTarget.value);
                        }}
                      />
                      <div className="button-box">
                        <button onClick={handleCookieUpdate} type="submit">
                          Submit
                        </button>
                        <button onClick={() => setShowCookieForm(false)}>Cancel</button>
                      </div>
                    </>
                  ) : (
                    <div>
                      <button onClick={() => setShowCookieForm(true)}>Update Cookie</button>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="info-box-item">
              <h2 id="sntegrations">Integrations</h2>
              <div className="settings-box-wrapper">
                <div>
                  <p>API token</p>
                </div>
                <div>
                  {showApiToken && <input readOnly value={apiToken} />}
                  <button onClick={() => setShowApiToken(!showApiToken)}>
                    {showApiToken ? 'Hide' : 'Show'}
                  </button>
                  {showApiToken && (
                    <Button
                      className="danger-button"
                      label="Revoke"
                      type="button"
                      onClick={async () => {
                        await deleteApiToken();
                        setShowApiToken(false);
                        setRefresh(true);
                      }}
                    />
                  )}
                </div>
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Enable returnyoutubedislike</p>
                </div>
                <ToggleConfig
                  name="downloads.integrate_ryd"
                  value={downloadDislikes}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div>
                  <p>Enable Sponsorblock</p>
                </div>
                <ToggleConfig
                  name="downloads.integrate_sponsorblock"
                  value={enableSponsorBlock}
                  updateCallback={handleUpdateConfig}
                />
              </div>
            </div>
            <div className="info-box-item">
              <h2>Snapshots</h2>
              <div className="settings-box-wrapper">
                <div>
                  <p>Enable Index Snapshot</p>
                </div>
                <ToggleConfig
                  name="application.enable_snapshot"
                  value={enableSnapshots}
                  updateCallback={handleUpdateConfig}
                />
              </div>
              <div className="settings-box-wrapper">
                <div></div>
                <div>
                  <div>
                    {appSettingsConfig?.application.enable_snapshot && snapshots && (
                      <>
                        <p>
                          Create next snapshot:{' '}
                          <span className="settings-current">{snapshots.next_exec_str}</span>,
                          snapshots expire after{' '}
                          <span className="settings-current">{snapshots.expire_after}</span>
                          . <br />
                          {isSnapshotQueued && <span>Snapshot in progress</span>}
                          {!isSnapshotQueued && (
                            <Button
                              label="Create snapshot now"
                              id="createButton"
                              onClick={async () => {
                                setIsSnapshotQueued(true);
                                await queueSnapshot();
                              }}
                            />
                          )}
                        </p>
                        <br />
                        {restoringSnapshot && <p>Snapshot restore started</p>}
                        {!restoringSnapshot &&
                          snapshots.snapshots &&
                          snapshots.snapshots.map(snapshot => {
                            return (
                              <p key={snapshot.id}>
                                <Button
                                  label="Restore"
                                  onClick={async () => {
                                    setRestoringSnapshot(true);
                                    await restoreSnapshot(snapshot.id);
                                  }}
                                />{' '}
                                Snapshot created on:{' '}
                                <span className="settings-current">{snapshot.start_date}</span>,
                                took{' '}
                                <span className="settings-current">{snapshot.duration_s}s</span> to
                                create. State: <i>{snapshot.state}</i>
                              </p>
                            );
                          })}
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <PaginationDummy />
    </>
  );
};

export default SettingsApplication;
