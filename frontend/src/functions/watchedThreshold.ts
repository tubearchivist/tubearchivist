function watchedThreshold(currentTime: number, duration: number) {
  let watched = false;

  if (duration <= 1800) {
    // If video is less than 30 min
    if (currentTime / duration >= 0.9) {
      // Mark as watched at 90%
      watched = true;
    }
  } else {
    // If video is more than 30 min
    if (currentTime >= duration - 120) {
      // Mark as watched if there is two minutes left
      watched = true;
    }
  }

  return watched;
}

export default watchedThreshold;
