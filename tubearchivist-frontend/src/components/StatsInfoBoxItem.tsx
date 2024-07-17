type StatsInfoBoxItemType = {
  title: string;
  card: Record<string, string | number | undefined>;
};

const StatsInfoBoxItem = ({ title, card }: StatsInfoBoxItemType) => {
  return (
    <div className="info-box-item">
      <h3>{title}</h3>
      <table className="agg-channel-table">
        <tbody>
          {Object.entries(card).map(([key, value], index) => {
            return (
              <tr key={index}>
                <td className="agg-channel-name">{key}: </td>
                <td className="agg-channel-right-align">{value}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default StatsInfoBoxItem;
