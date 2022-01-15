# Tube Archivist Companion
A browser extension to directly add videos from YouTube to Tube Archivist.

## MVP or better *bearly viable product*
This is a proof of concept with the following functionality:
- Add your Tube Archivist connection details in the addon popup
- Inject a download button into youtube search results page
- Clicking the button will automatically add the video to the your download queue

## Test this extension
- Firefox
  - Open `about:debugging#/runtime/this-firefox`
  - Click on *Load Temporary Add-on*
  - Select the *manifest.json* file to load the addon. 
- Chrome / Chromium
  - Open `chrome://extensions/`
  - Toggle *Developer mode* on top right
  - Click on *Load unpacked*
  - Open the folder containing the *manifest.json* file.

## Help needed
This is only minimally useful in this state. Join us on our Discord and please help us improve that.

## Note:
- For mysterious reasons sometimes the download buttons will only load when refreshing the YouTube search page and not on first load... Hence: Help needed!
- For your testing environment only for now: Point the extension to the newest *unstable* build.
