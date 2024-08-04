import { Helmet } from 'react-helmet';
import { useParams } from 'react-router-dom';

const ChannelStream = () => {
  const { channelId } = useParams();

  return (
    <>
      <Helmet>
        <title>TA | Channel: {channel.channel_name}</title>
      </Helmet>
    </>
  );
};

export default ChannelStream;
