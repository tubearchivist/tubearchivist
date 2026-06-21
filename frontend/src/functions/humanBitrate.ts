/**
 * Format a bitrate (in bits per second) as human-readable text.
 *
 * Bitrate values from yt-dlp come in bits per second. This helper formats
 * them using SI powers of 1000 (kbps, Mbps, Gbps) — the standard for
 * bit-rate display, where 1 kbps = 1000 bits per second.
 *
 * Note: this intentionally does NOT use the IEC "Kib/s" unit, since
 * network bitrates (and yt-dlp's own `--format-sort bitrate` values)
 * are universally expressed in SI decimal units in the wild.
 *
 * @param bitsPerSecond Bitrate in bits per second.
 * @param dp Number of decimal places to display. Default 1.
 *
 * @return Formatted string ending in the unit (e.g. "1.5 Mbps").
 */
function humanBitrate(bitsPerSecond: number, dp = 1): string {
  if (!isFinite(bitsPerSecond) || bitsPerSecond < 0) {
    return '-';
  }
  if (bitsPerSecond === 0) {
    return '0 bps';
  }

  const thresh = 1000;
  const units = ['bps', 'kbps', 'Mbps', 'Gbps', 'Tbps'];

  if (Math.abs(bitsPerSecond) < thresh) {
    return bitsPerSecond + ' bps';
  }

  let value = bitsPerSecond;
  let u = 0;
  const r = 10 ** dp;

  do {
    value /= thresh;
    ++u;
  } while (Math.round(Math.abs(value) * r) / r >= thresh && u < units.length - 1);

  return value.toFixed(dp) + ' ' + units[u];
}

export default humanBitrate;
