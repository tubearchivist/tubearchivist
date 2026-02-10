#!/command/with-contenv bash
. $(dirname "$0")/base.sh

# update yt-dlp if needed
if [[ "${TA_AUTO_UPDATE_YTDLP,,}" =~ ^(release|nightly)$ ]]; then
    echo "Updating yt-dlp..."
    preflag=$([[ "${TA_AUTO_UPDATE_YTDLP,,}" == "nightly" ]] && echo "--pre" || echo "")
    python -m pip install --target=/root/.local/bin --upgrade $preflag "yt-dlp[default]" || {
        echo "yt-dlp update failed"
    }
fi
