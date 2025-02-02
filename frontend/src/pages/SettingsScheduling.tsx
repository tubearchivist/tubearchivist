import Notifications from '../components/Notifications';
import SettingsNavigation from '../components/SettingsNavigation';
import Button from '../components/Button';
import PaginationDummy from '../components/PaginationDummy';
import { Fragment, useEffect, useState } from 'react';
import loadSchedule, { ScheduleResponseType } from '../api/loader/loadSchedule';
import loadAppriseNotification, {
  AppriseNotificationType,
} from '../api/loader/loadAppriseNotification';
import deleteTaskSchedule from '../api/actions/deleteTaskSchedule';
import createTaskSchedule from '../api/actions/createTaskSchedule';
import createAppriseNotificationUrl, {
  AppriseTaskNameType,
} from '../api/actions/createAppriseNotificationUrl';
import deleteAppriseNotificationUrl from '../api/actions/deleteAppriseNotificationUrl';
import { ApiError } from '../functions/APIClient';

const SettingsScheduling = () => {
  const [refresh, setRefresh] = useState(false);

  const [scheduleResponse, setScheduleResponse] = useState<ScheduleResponseType>([]);
  const [appriseNotification, setAppriseNotification] = useState<AppriseNotificationType>();

  const [updateSubscribed, setUpdateSubscribed] = useState<string | undefined>();
  const [downloadPending, setDownloadPending] = useState<string | undefined>();
  const [checkReindex, setCheckReindex] = useState<string | undefined>();
  const [checkReindexDays, setCheckReindexDays] = useState<number | undefined>();
  const [thumbnailCheck, setThumbnailCheck] = useState<string | undefined>();
  const [zipBackup, setZipBackup] = useState<string | undefined>();
  const [zipBackupDays, setZipBackupDays] = useState<number | undefined>();
  const [notificationUrl, setNotificationUrl] = useState<string | undefined>();
  const [notificationTask, setNotificationTask] = useState<AppriseTaskNameType | string>('');
  const [checkReindexError, setCheckReindexError] = useState<string | null>(null);
  const [updateSubscribedError, setUpdateSubscribedError] = useState<string | null>(null);
  const [downloadPendingError, setDownloadPendingError] = useState<string | null>(null);
  const [thumnailCheckError, setThumnailCheckError] = useState<string | null>(null);
  const [zipBackupError, setZipBackupError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      if (refresh) {
        const scheduleResponse = await loadSchedule();
        const appriseNotificationResponse = await loadAppriseNotification();

        setScheduleResponse(scheduleResponse);
        setAppriseNotification(appriseNotificationResponse);

        setRefresh(false);
      }
    })();
  }, [refresh]);

  useEffect(() => {
    setRefresh(true);
  }, []);

  const groupedSchedules = Object.groupBy(scheduleResponse, ({ name }) => name);

  console.log(groupedSchedules);

  const { update_subscribed, download_pending, run_backup, check_reindex, thumbnail_check } =
    groupedSchedules;

  const updateSubscribedSchedule = update_subscribed?.pop();
  const downloadPendingSchedule = download_pending?.pop();
  const runBackup = run_backup?.pop();
  const checkReindexSchedule = check_reindex?.pop();
  const thumbnailCheckSchedule = thumbnail_check?.pop();

  return (
    <>
      <title>TA | Scheduling Settings</title>
      <div className="boxed-content">
        <SettingsNavigation />
        <Notifications pageName={'all'} />

        <div className="title-bar">
          <h1>Scheduler Setup</h1>
          <div className="settings-group">
            <p>
              Schedule settings expect a cron like format, where the first value is minute, second
              is hour and third is day of the week.
            </p>
            <p>Examples:</p>
            <ul>
              <li>
                <span className="settings-current">0 15 *</span>: Run task every day at 15:00 in the
                afternoon.
              </li>
              <li>
                <span className="settings-current">30 8 */2</span>: Run task every second day of the
                week (Sun, Tue, Thu, Sat) at 08:30 in the morning.
              </li>
              <li>
                <span className="settings-current">auto</span>: Sensible default.
              </li>
            </ul>
            <p>Note:</p>
            <ul>
              <li>
                Avoid an unnecessary frequent schedule to not get blocked by YouTube. For that
                reason, the scheduler doesn't support schedules that trigger more than once per
                hour.
              </li>
            </ul>
          </div>
        </div>

        <div className="settings-group">
          <h2>Rescan Subscriptions</h2>
          <div className="settings-item">
            <p>
              Become a sponsor and join{' '}
              <a href="https://members.tubearchivist.com/" target="_blank">
                members.tubearchivist.com
              </a>{' '}
              to get access to <span className="settings-current">real time</span> notifications for
              new videos uploaded by your favorite channels.
            </p>
            <p>
              Current rescan schedule:{' '}
              <span className="settings-current">
                {!updateSubscribedSchedule && 'False'}
                {updateSubscribedSchedule && (
                  <>
                    {updateSubscribedSchedule?.schedule}{' '}
                    <Button
                      label="Delete"
                      data-schedule="update_subscribed"
                      onClick={async () => {
                        await deleteTaskSchedule('update_subscribed');

                        setRefresh(true);
                      }}
                      className="danger-button"
                    />
                  </>
                )}
              </span>
            </p>
            <p>Periodically rescan your subscriptions:</p>

            <input
              type="text"
              value={updateSubscribed || updateSubscribedSchedule?.schedule || ''}
              onChange={e => {
                setUpdateSubscribed(e.currentTarget.value);
              }}
            />
            <Button
              label="Save"
              onClick={async () => {
                try {
                  await createTaskSchedule('update_subscribed', {
                    schedule: updateSubscribed,
                  });
                  setUpdateSubscribedError('');
                } catch (error) {
                  const apiError = error as ApiError;
                  if (apiError.status && apiError.message) {
                    setUpdateSubscribedError(`Error ${apiError.status}: ${apiError.message}`);
                  } else {
                    setUpdateSubscribedError('An unexpected error occurred.');
                  }
                }
                setUpdateSubscribed('');
                setRefresh(true);
              }}
            />
            {updateSubscribedError && <p className="danger-zone">{updateSubscribedError}</p>}
          </div>
        </div>
        <div className="settings-group">
          <h2>Start Download</h2>
          <div className="settings-item">
            <p>
              Current Download schedule:{' '}
              <span className="settings-current">
                {!download_pending && 'False'}
                {downloadPendingSchedule && (
                  <>
                    {downloadPendingSchedule?.schedule}{' '}
                    <Button
                      label="Delete"
                      className="danger-button"
                      onClick={async () => {
                        await deleteTaskSchedule('download_pending');

                        setRefresh(true);
                      }}
                    />
                  </>
                )}
              </span>
            </p>
            <p>Automatic video download schedule:</p>

            <input
              type="text"
              value={downloadPending || downloadPendingSchedule?.schedule || ''}
              onChange={e => {
                setDownloadPending(e.currentTarget.value);
              }}
            />
            <Button
              label="Save"
              onClick={async () => {
                try {
                  await createTaskSchedule('download_pending', {
                    schedule: downloadPending,
                  });
                  setDownloadPendingError('');
                } catch (error) {
                  const apiError = error as ApiError;
                  if (apiError.status && apiError.message) {
                    setDownloadPendingError(`Error ${apiError.status}: ${apiError.message}`);
                  } else {
                    setDownloadPendingError('An unexpected error occurred.');
                  }
                }
                setDownloadPending('');
                setRefresh(true);
              }}
            />
            {downloadPendingError && <p className="danger-zone">{downloadPendingError}</p>}
          </div>
        </div>

        <div className="settings-group">
          <h2>Refresh Metadata</h2>
          <div className="settings-item">
            <p>
              Current Metadata refresh schedule:{' '}
              <span className="settings-current">
                {!checkReindexSchedule && 'False'}
                {checkReindexSchedule && (
                  <>
                    {checkReindexSchedule?.schedule}{' '}
                    <Button
                      label="Delete"
                      className="danger-button"
                      onClick={async () => {
                        await deleteTaskSchedule('check_reindex');

                        setRefresh(true);
                      }}
                    />
                  </>
                )}
              </span>
            </p>
            <p>Daily schedule to refresh metadata from YouTube:</p>

            <input
              type="text"
              value={checkReindex || checkReindexSchedule?.schedule || ''}
              onChange={e => {
                setCheckReindex(e.currentTarget.value);
              }}
            />
            <Button
              label="Save"
              onClick={async () => {
                try {
                  await createTaskSchedule('check_reindex', {
                    schedule: checkReindex,
                  });
                  setCheckReindexError('');
                } catch (error) {
                  const apiError = error as ApiError;
                  if (apiError.status && apiError.message) {
                    setCheckReindexError(`Error ${apiError.status}: ${apiError.message}`);
                  } else {
                    setCheckReindexError('An unexpected error occurred.');
                  }
                }
                setCheckReindex('');
                setRefresh(true);
              }}
            />
            {checkReindexError && <p className="danger-zone">{checkReindexError}</p>}
          </div>
          <div className="settings-item">
            <p>
              Current refresh for metadata older than x days:{' '}
              <span className="settings-current">{checkReindexSchedule?.config?.days}</span>
            </p>
            <p>Refresh older than x days, recommended 90:</p>

            <input
              type="number"
              value={checkReindexDays || checkReindexSchedule?.config?.days || 0}
              onChange={e => {
                setCheckReindexDays(Number(e.currentTarget.value));
              }}
            />
            <Button
              label="Save"
              onClick={async () => {
                await createTaskSchedule('check_reindex', {
                  config: {
                    days: checkReindexDays,
                  },
                });

                setCheckReindexDays(undefined);

                setRefresh(true);
              }}
            />
          </div>
        </div>

        <div className="settings-group">
          <h2>Thumbnail Check</h2>
          <div className="settings-item">
            <p>
              Current thumbnail check schedule:{' '}
              <span className="settings-current">
                {!thumbnailCheckSchedule && 'False'}
                {thumbnailCheckSchedule && (
                  <>
                    {thumbnailCheckSchedule?.schedule}{' '}
                    <Button
                      label="Delete"
                      className="danger-button"
                      onClick={async () => {
                        await deleteTaskSchedule('thumbnail_check');

                        setRefresh(true);
                      }}
                    />
                  </>
                )}
              </span>
            </p>
            <p>Periodically check and cleanup thumbnails:</p>

            <input
              type="text"
              value={thumbnailCheck || thumbnailCheckSchedule?.schedule || ''}
              onChange={e => {
                setThumbnailCheck(e.currentTarget.value);
              }}
            />
            <Button
              label="Save"
              onClick={async () => {
                try {
                  await createTaskSchedule('thumbnail_check', {
                    schedule: thumbnailCheck,
                  });
                  setThumnailCheckError('');
                } catch (error) {
                  const apiError = error as ApiError;
                  if (apiError.status && apiError.message) {
                    setThumnailCheckError(`Error ${apiError.status}: ${apiError.message}`);
                  } else {
                    setThumnailCheckError('An unexpected error occurred.');
                  }
                }
                setThumbnailCheck('');
                setRefresh(true);
              }}
            />
            {thumnailCheckError && <p className="danger-zone">{thumnailCheckError}</p>}
          </div>
        </div>
        <div className="settings-group">
          <h2>ZIP file index backup</h2>
          <div className="settings-item">
            <p>
              <i>
                Zip file backups are very slow for large archives and consistency is not guaranteed,
                use snapshots instead. Make sure no other tasks are running when creating a Zip file
                backup.
              </i>
            </p>
            <p>
              Current index backup schedule:{' '}
              <span className="settings-current">
                {!runBackup && 'False'}
                {runBackup && (
                  <>
                    {runBackup.schedule}{' '}
                    <Button
                      label="Delete"
                      className="danger-button"
                      onClick={async () => {
                        await deleteTaskSchedule('run_backup');

                        setRefresh(true);
                      }}
                    />
                  </>
                )}
              </span>
            </p>
            <p>Automatically backup metadata to a zip file:</p>

            <input
              type="text"
              value={zipBackup || runBackup?.schedule || ''}
              onChange={e => {
                setZipBackup(e.currentTarget.value);
              }}
            />
            <Button
              label="Save"
              onClick={async () => {
                try {
                  await createTaskSchedule('run_backup', {
                    schedule: zipBackup,
                  });
                  setZipBackupError('');
                } catch (error) {
                  const apiError = error as ApiError;
                  if (apiError.status && apiError.message) {
                    setZipBackupError(`Error ${apiError.status}: ${apiError.message}`);
                  } else {
                    setZipBackupError('An unexpected error occurred.');
                  }
                }
                setZipBackup('');
                setRefresh(true);
              }}
            />
            {zipBackupError && <p className="danger-zone">{zipBackupError}</p>}
          </div>
          <div className="settings-item">
            <p>
              Current backup files to keep:{' '}
              <span className="settings-current">{runBackup?.config?.rotate}</span>
            </p>
            <p>Max auto backups to keep:</p>

            <input
              type="number"
              value={(zipBackupDays || runBackup?.config?.rotate)?.toString() || 0}
              onChange={e => {
                setZipBackupDays(Number(e.currentTarget.value));
              }}
            />
            <Button
              label="Save"
              onClick={async () => {
                await createTaskSchedule('run_backup', {
                  config: {
                    rotate: zipBackupDays,
                  },
                });

                setZipBackupDays(undefined);

                setRefresh(true);
              }}
            />
          </div>
        </div>
        <div className="settings-group">
          <h2>Add Notification URL</h2>
          <div className="settings-item">
            {!appriseNotification && <p>No notifications stored</p>}
            {appriseNotification && (
              <>
                <div className="description-text">
                  {Object.entries(appriseNotification)?.map(([key, { urls, title }]) => {
                    return (
                      <Fragment key={key}>
                        <h3>{title}</h3>

                        {urls.map((url: string) => {
                          return (
                            <p key={`${key}_${url}`}>
                              <span>{url} </span>
                              <Button
                                type="button"
                                className="danger-button"
                                label="Delete"
                                onClick={async () => {
                                  await deleteAppriseNotificationUrl(key as AppriseTaskNameType);

                                  setRefresh(true);
                                }}
                              />
                            </p>
                          );
                        })}
                      </Fragment>
                    );
                  })}
                </div>
              </>
            )}
          </div>

          <div className="settings-item">
            <p>
              <i>
                Send notification on completed tasks with the help of the{' '}
                <a href="https://github.com/caronc/apprise" target="_blank">
                  Apprise
                </a>{' '}
                library.
              </i>
            </p>

            <select
              value={notificationTask}
              onChange={e => {
                setNotificationTask(e.currentTarget.value);
              }}
            >
              <option value="">-- select task --</option>
              <option value="update_subscribed">Rescan your Subscriptions</option>
              <option value="extract_download">Add to download queue</option>
              <option value="download_pending">Downloading</option>
              <option value="check_reindex">Reindex Documents</option>
            </select>

            <input
              type="text"
              placeholder="Apprise notification URL"
              value={notificationUrl || ''}
              onChange={e => {
                setNotificationUrl(e.currentTarget.value);
              }}
            />

            <Button
              label="Save"
              onClick={async () => {
                await createAppriseNotificationUrl(
                  notificationTask as AppriseTaskNameType,
                  notificationUrl || '',
                );

                setRefresh(true);
              }}
            />
          </div>
        </div>

        <PaginationDummy />
      </div>
    </>
  );
};

export default SettingsScheduling;
