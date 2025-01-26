import { useEffect, useState } from 'react';
import loadBackupList from '../api/loader/loadBackupList';
import SettingsNavigation from '../components/SettingsNavigation';
import deleteDownloadQueueByFilter from '../api/actions/deleteDownloadQueueByFilter';
import updateTaskByName from '../api/actions/updateTaskByName';
import queueBackup from '../api/actions/queueBackup';
import restoreBackup from '../api/actions/restoreBackup';
import Notifications from '../components/Notifications';
import Button from '../components/Button';

type Backup = {
  filename: string;
  file_path: string;
  file_size: number;
  timestamp: string;
  reason: string;
};

type BackupListType = Backup[];

const SettingsActions = () => {
  const [deleteIgnored, setDeleteIgnored] = useState(false);
  const [deletePending, setDeletePending] = useState(false);
  const [processingImports, setProcessingImports] = useState(false);
  const [reEmbed, setReEmbed] = useState(false);
  const [backupStarted, setBackupStarted] = useState(false);
  const [isRestoringBackup, setIsRestoringBackup] = useState(false);
  const [reScanningFileSystem, setReScanningFileSystem] = useState(false);

  const [backupListResponse, setBackupListResponse] = useState<BackupListType>();

  const backups = backupListResponse;
  const hasBackups = !!backups && backups?.length > 0;

  useEffect(() => {
    (async () => {
      const backupListResponse = await loadBackupList();

      setBackupListResponse(backupListResponse);
    })();
  }, []);

  return (
    <>
      <title>TA | Actions</title>
      <div className="boxed-content">
        <SettingsNavigation />
        <Notifications
          pageName={'all'}
          update={
            deleteIgnored ||
            deletePending ||
            processingImports ||
            reEmbed ||
            backupStarted ||
            isRestoringBackup ||
            reScanningFileSystem
          }
          setShouldRefresh={() => {
            setDeleteIgnored(false);
            setDeletePending(false);
            setProcessingImports(false);
            setReEmbed(false);
            setBackupStarted(false);
            setIsRestoringBackup(false);
            setReScanningFileSystem(false);
          }}
        />

        <div className="title-bar">
          <h1>Actions</h1>
        </div>
        <div className="settings-group">
          <h2>Delete download queue</h2>
          <p>Delete your pending or previously ignored videos from your download queue.</p>
          {deleteIgnored && <p>Deleting download queue: ignored</p>}
          {!deleteIgnored && (
            <Button
              label="Delete all ignored"
              title="Delete all previously ignored videos from the queue"
              onClick={async () => {
                await deleteDownloadQueueByFilter('ignore');
                setDeleteIgnored(true);
              }}
            />
          )}{' '}
          {deletePending && <p>Deleting download queue: pending</p>}
          {!deletePending && (
            <Button
              label="Delete all queued"
              title="Delete all pending videos from the queue"
              onClick={async () => {
                await deleteDownloadQueueByFilter('pending');
                setDeletePending(true);
              }}
            />
          )}
        </div>
        <div className="settings-group">
          <h2>Manual media files import.</h2>
          <p>
            Add files to the <span className="settings-current">cache/import</span> folder. Make
            sure to follow the instructions in the Github{' '}
            <a
              href="https://docs.tubearchivist.com/settings/actions/#manual-media-files-import"
              target="_blank"
            >
              Wiki
            </a>
            .
          </p>
          <div id="manual-import">
            {processingImports && <p>Processing import</p>}
            {!processingImports && (
              <Button
                label="Start import"
                onClick={async () => {
                  await updateTaskByName('manual_import');
                  setProcessingImports(true);
                }}
              />
            )}
          </div>
        </div>
        <div className="settings-group">
          <h2>Embed thumbnails into media file.</h2>
          <p>Set extracted youtube thumbnail as cover art of the media file.</p>
          <div id="re-embed">
            {reEmbed && <p>Processing thumbnails</p>}
            {!reEmbed && (
              <Button
                label="Start process"
                onClick={async () => {
                  await updateTaskByName('resync_thumbs');
                  setReEmbed(true);
                }}
              />
            )}
          </div>
        </div>
        <div className="settings-group">
          <h2>ZIP file index backup</h2>
          <p>
            Export your database to a zip file stored at{' '}
            <span className="settings-current">cache/backup</span>.
          </p>
          <p>
            <i>
              Zip file backups are very slow for large archives and consistency is not guaranteed,
              use snapshots instead. Make sure no other tasks are running when creating a Zip file
              backup.
            </i>
          </p>
          <div id="db-backup">
            {backupStarted && <p>Backing up archive</p>}
            {!backupStarted && (
              <Button
                label="Start backup"
                onClick={async () => {
                  await queueBackup();
                  setBackupStarted(true);
                }}
              />
            )}
          </div>
        </div>
        <div className="settings-group">
          <h2>Restore from backup</h2>
          <p>
            <span className="danger-zone">Danger Zone</span>: This will replace your existing index
            with the backup.
          </p>
          <p>
            Restore from available backup files from{' '}
            <span className="settings-current">cache/backup</span>.
          </p>
          {!hasBackups && <p>No backups found.</p>}
          {hasBackups && (
            <>
              <div className="backup-grid-row">
                <span></span>
                <span>Timestamp</span>
                <span>Source</span>
                <span>Filename</span>
              </div>
              {isRestoringBackup && <p>Restoring from backup</p>}
              {!isRestoringBackup &&
                backups.map(backup => {
                  return (
                    <div key={backup.filename} id={backup.filename} className="backup-grid-row">
                      <Button
                        label="Restore"
                        onClick={async () => {
                          await restoreBackup(backup.filename);
                          setIsRestoringBackup(true);
                        }}
                      />
                      <span>{backup.timestamp}</span>
                      <span>{backup.reason}</span>
                      <span>{backup.filename}</span>
                    </div>
                  );
                })}
            </>
          )}
        </div>
        <div className="settings-group">
          <h2>Rescan filesystem</h2>
          <p>
            <span className="danger-zone">Danger Zone</span>: This will delete the metadata of
            deleted videos from the filesystem.
          </p>
          <p>
            Rescan your media folder looking for missing videos and clean up index. More infos on
            the Github{' '}
            <a
              href="https://docs.tubearchivist.com/settings/actions/#rescan-filesystem"
              target="_blank"
            >
              Wiki
            </a>
            .
          </p>
          <div id="fs-rescan">
            {reScanningFileSystem && <p>File system scan in progress</p>}
            {!reScanningFileSystem && (
              <Button
                label="Rescan filesystem"
                onClick={async () => {
                  await updateTaskByName('rescan_filesystem');
                  setReScanningFileSystem(true);
                }}
              />
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default SettingsActions;
