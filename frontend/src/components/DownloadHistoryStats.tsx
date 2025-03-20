import humanFileSize from '../functions/humanFileSize';
import formatDate from '../functions/formatDates';
import formatNumbers from '../functions/formatNumbers';
import { DownloadHistoryStatsType } from '../api/loader/loadStatsDownloadHistory';

type DownloadHistoryStatsProps = {
  downloadHistoryStats?: DownloadHistoryStatsType;
  useSIUnits: boolean;
};

const DownloadHistoryStats = ({ downloadHistoryStats, useSIUnits }: DownloadHistoryStatsProps) => {
  if (!downloadHistoryStats) {
    return <p id="loading">Loading...</p>;
  }

  if (downloadHistoryStats.length === 0) {
    return (
      <div className="info-box-item">
        <h3>No recent downloads</h3>
      </div>
    );
  }

  return downloadHistoryStats.map(({ date, count, media_size }) => {
    const videoText = count === 1 ? 'Video' : 'Videos';
    const intlDate = formatDate(date);

    return (
      <div key={date} className="info-box-item">
        <h3>{intlDate}</h3>
        <p>
          +{formatNumbers(count)} {videoText}
          <br />
          {humanFileSize(media_size, useSIUnits)}
        </p>
      </div>
    );
  });
};

export default DownloadHistoryStats;
