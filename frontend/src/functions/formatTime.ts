// Formats times in seconds for frontend
function formatTime(time: number) {
  const hoursUnformatted = time / 3600;
  const minutesUnformatted = (time % 3600) / 60;
  const secondsUnformatted = time % 60;

  const hoursFormatted = Math.trunc(hoursUnformatted);
  let minutesFormatted;

  if (minutesUnformatted < 10 && hoursFormatted > 0) {
    minutesFormatted = '0' + Math.trunc(minutesUnformatted);
  } else {
    minutesFormatted = Math.trunc(minutesUnformatted).toString();
  }

  let secondsFormatted;
  if (secondsUnformatted < 10) {
    secondsFormatted = '0' + Math.trunc(secondsUnformatted);
  } else {
    secondsFormatted = Math.trunc(secondsUnformatted).toString();
  }

  let timeUnformatted = '';
  if (hoursFormatted > 0) {
    timeUnformatted = hoursFormatted + ':';
  }

  const timeFormatted = timeUnformatted.concat(minutesFormatted, ':', secondsFormatted);
  return timeFormatted;
}

export default formatTime;
