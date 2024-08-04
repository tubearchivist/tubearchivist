import humanFileSize from '../functions/humanFileSize';
import formatNumbers from '../functions/formatNumbers';
import { Link } from 'react-router-dom';
import Routes from '../configuration/routes/RouteList';
import { BiggestChannelsStatsType } from '../pages/SettingsDashboard';

type BiggestChannelsStatsProps = {
  biggestChannelsStatsByCount?: BiggestChannelsStatsType;
  biggestChannelsStatsByDuration?: BiggestChannelsStatsType;
  biggestChannelsStatsByMediaSize?: BiggestChannelsStatsType;
  useSI: boolean;
};

const BiggestChannelsStats = ({
  biggestChannelsStatsByCount,
  biggestChannelsStatsByDuration,
  biggestChannelsStatsByMediaSize,
  useSI,
}: BiggestChannelsStatsProps) => {
  if (
    !biggestChannelsStatsByCount &&
    !biggestChannelsStatsByDuration &&
    !biggestChannelsStatsByMediaSize
  ) {
    return <p id="loading">Loading...</p>;
  }

  return (
    <>
      <div className="info-box-item">
        <table className="agg-channel-table">
          <thead>
            <tr>
              <th>Name</th>
              <th className="agg-channel-right-align">Videos</th>
            </tr>
          </thead>

          <tbody>
            {biggestChannelsStatsByCount &&
              biggestChannelsStatsByCount.map(({ id, name, doc_count }) => {
                return (
                  <tr key={id}>
                    <td className="agg-channel-name">
                      <Link to={Routes.Channel(id)}>{name}</Link>
                    </td>
                    <td className="agg-channel-right-align">{formatNumbers(doc_count)}</td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      <div className="info-box-item">
        <table className="agg-channel-table">
          <thead>
            <tr>
              <th>Name</th>
              <th className="agg-channel-right-align">Duration</th>
            </tr>
          </thead>

          <tbody>
            {biggestChannelsStatsByDuration &&
              biggestChannelsStatsByDuration.map(({ id, name, duration_str }) => {
                return (
                  <tr key={id}>
                    <td className="agg-channel-name">
                      <Link to={Routes.Channel(id)}>{name}</Link>
                    </td>
                    <td className="agg-channel-right-align">{duration_str}</td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>

      <div className="info-box-item">
        <table className="agg-channel-table">
          <thead>
            <tr>
              <th>Name</th>
              <th className="agg-channel-right-align">Media Size</th>
            </tr>
          </thead>

          <tbody>
            {biggestChannelsStatsByMediaSize &&
              biggestChannelsStatsByMediaSize.map(({ id, name, media_size }) => {
                return (
                  <tr key={id}>
                    <td className="agg-channel-name">
                      <Link to={Routes.Channel(id)}>{name}</Link>
                    </td>
                    <td className="agg-channel-right-align">{humanFileSize(media_size, useSI)}</td>
                  </tr>
                );
              })}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default BiggestChannelsStats;
