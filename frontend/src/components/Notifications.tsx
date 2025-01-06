import { Fragment, useEffect, useState } from 'react';
import loadNotifications, { NotificationPages } from '../api/loader/loadNotifications';
import iconStop from '/img/icon-stop.svg';
import stopTaskByName from '../api/actions/stopTaskByName';

type NotificationType = {
  title: string;
  group: string;
  api_stop: boolean;
  level: string;
  id: string;
  command: boolean | string;
  messages: string[];
  progress: number;
};

type NotificationResponseType = NotificationType[];

type NotificationsProps = {
  pageName: NotificationPages;
  includeReindex?: boolean;
  update?: boolean;
  setShouldRefresh?: (isDone: boolean) => void;
};

const Notifications = ({
  pageName,
  includeReindex = false,
  update,
  setShouldRefresh,
}: NotificationsProps) => {
  const [notificationResponse, setNotificationResponse] = useState<NotificationResponseType>([]);

  useEffect(() => {
    const intervalId = setInterval(async () => {
      const notifications = await loadNotifications(pageName, includeReindex);

      if (notifications.length === 0) {
        setNotificationResponse(notifications);
        clearInterval(intervalId);
        setShouldRefresh?.(true);
        return;
      } else {
        setShouldRefresh?.(false);
      }

      setNotificationResponse(notifications);
    }, 500);

    return () => {
      clearInterval(intervalId);
    };
  }, [pageName, update, setShouldRefresh, includeReindex]);

  if (notificationResponse.length === 0) {
    return [];
  }

  return (
    <>
      {notificationResponse.map(notification => (
        <div
          id={notification.id}
          className={`notification ${notification.level}`}
          key={notification.id}
        >
          <h3>{notification.title}</h3>
          <p>
            {notification.messages.map?.(message => {
              return (
                <Fragment key={message}>
                  {message}
                  <br />
                </Fragment>
              );
            }) || notification.messages}
          </p>
          <div className="task-control-icons">
            {notification['api_stop'] && notification.command !== 'STOP' && (
              <img
                src={iconStop}
                id="stop-icon"
                title="Stop Task"
                alt="stop icon"
                onClick={async () => {
                  await stopTaskByName(notification.id);
                }}
              />
            )}
          </div>
          <div
            className="notification-progress-bar"
            style={{ width: `${notification.progress * 100 || 0}%` }}
          ></div>
        </div>
      ))}
    </>
  );
};

export default Notifications;
