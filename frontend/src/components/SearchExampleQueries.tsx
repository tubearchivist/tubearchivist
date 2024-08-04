const SearchExampleQueries = () => {
  return (
    <div id="multi-search-results-placeholder">
      <div>
        <h2>Example queries</h2>
        <ul>
          <li>
            <span className="value">music video</span> — basic search
          </li>
          <li>
            <span>video: active:</span>
            <span className="value">no</span> — all videos deleted from YouTube
          </li>
          <li>
            <span>video:</span>
            <span className="value">learn javascript</span>
            <span> channel:</span>
            <span className="value">corey schafer</span>
            <span> active:</span>
            <span className="value">yes</span>
          </li>
          <li>
            <span>channel:</span>
            <span className="value">linux</span>
            <span> subscribed:</span>
            <span className="value">yes</span>
          </li>
          <li>
            <span>playlist:</span>
            <span className="value">backend engineering</span>
            <span> active:</span>
            <span className="value">yes</span>
            <span> subscribed:</span>
            <span className="value">yes</span>
          </li>
        </ul>
      </div>
      <div>
        <h2>Keywords cheatsheet</h2>
        <p>
          For detailed usage check{' '}
          <a href="https://docs.tubearchivist.com/search/" target="_blank">
            wiki
          </a>
          .
        </p>
        <div>
          <ul>
            <li>
              <span>simple:</span> (implied) — search in video titles, channel names and playlist
              titles
            </li>
            <li>
              <span>video:</span> — search in video titles, tags and category field
              <ul>
                <li>
                  <span>channel:</span> — channel name
                </li>
                <li>
                  <span>active:</span>
                  <span className="value">yes/no</span> — whether the video is still active on
                  YouTube
                </li>
              </ul>
            </li>
            <li>
              <span>channel:</span> — search in channel name and channel description
              <ul>
                <li>
                  <span>subscribed:</span>
                  <span className="value">yes/no</span> — whether you are subscribed to the channel
                </li>
                <li>
                  <span>active:</span>
                  <span className="value">yes/no</span> — whether the video is still active on
                  YouTube
                </li>
              </ul>
            </li>
            <li>
              <span>playlist:</span> — search in channel name and channel description
              <ul>
                <li>
                  <span>subscribed:</span>
                  <span className="value">yes/no</span> — whether you are subscribed to the channel
                </li>
                <li>
                  <span>active:</span>
                  <span className="value">yes/no</span> — whether the video is still active on
                  YouTube
                </li>
              </ul>
            </li>
            <li>
              <span>full:</span> — search in video subtitles
              <ul>
                <li>
                  <span>lang:</span> — subtitles language (use two-letter ISO country code, same as
                  the one from settings page)
                </li>
                <li>
                  <span>source:</span>
                  <span className="value">auto/user</span> — <i>auto</i> to search though
                  auto-generated subtitles only, or <i>user</i> to search through user-uploaded
                  subtitles only
                </li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default SearchExampleQueries;
