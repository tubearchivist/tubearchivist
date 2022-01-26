
function sortChange(sortValue) {
    var payload = JSON.stringify({'sort_order': sortValue});
    sendPost(payload);
    setTimeout(function(){
        location.reload();
        return false;
    }, 500);
}

function isWatched(youtube_id) {
    // sendVideoProgress(youtube_id, 0); // Reset video progress on watched;
    var payload = JSON.stringify({'watched': youtube_id});
    sendPost(payload);
    var seenIcon = document.createElement('img');
    seenIcon.setAttribute('src', "/static/img/icon-seen.svg");
    seenIcon.setAttribute('alt', 'seen-icon');
    seenIcon.setAttribute('id', youtube_id);
    seenIcon.setAttribute('title', "Mark as unwatched");
    seenIcon.setAttribute('onclick', "isUnwatched(this.id)");
    seenIcon.classList = 'seen-icon';
    document.getElementById(youtube_id).replaceWith(seenIcon);
}

function isWatchedButton(button) {
    youtube_id = button.getAttribute("data-id");
    var payload = JSON.stringify({'watched': youtube_id});
    button.remove();
    sendPost(payload);
    setTimeout(function(){
        location.reload();
        return false;
    }, 1000);
}

function isUnwatched(youtube_id) {
    // sendVideoProgress(youtube_id, 0); // Reset video progress on unwatched;
    var payload = JSON.stringify({'un_watched': youtube_id});
    sendPost(payload);
    var unseenIcon = document.createElement('img');
    unseenIcon.setAttribute('src', "/static/img/icon-unseen.svg");
    unseenIcon.setAttribute('alt', 'unseen-icon');
    unseenIcon.setAttribute('id', youtube_id);
    unseenIcon.setAttribute('title', "Mark as watched");
    unseenIcon.setAttribute('onclick', "isWatched(this.id)");
    unseenIcon.classList = 'unseen-icon';
    document.getElementById(youtube_id).replaceWith(unseenIcon);
}

function unsubscribe(id_unsub) {
    var payload = JSON.stringify({'unsubscribe': id_unsub});
    sendPost(payload);
    var message = document.createElement('span');
    message.innerText = "You are unsubscribed.";
    document.getElementById(id_unsub).replaceWith(message);
}

function subscribe(id_sub) {
    var payload = JSON.stringify({'subscribe': id_sub});
    sendPost(payload);
    var message = document.createElement('span');
    message.innerText = "You are subscribed.";
    document.getElementById(id_sub).replaceWith(message);
}

function changeView(image) {
    var sourcePage = image.getAttribute("data-origin");
    var newView = image.getAttribute("data-value");
    var payload = JSON.stringify({'change_view': sourcePage + ":" + newView});
    sendPost(payload);
    setTimeout(function(){
        location.reload();
        return false;
    }, 500);
}

function toggleCheckbox(checkbox) {
    // pass checkbox id as key and checkbox.checked as value
    var toggleId = checkbox.id;
    var toggleVal = checkbox.checked;
    var payloadDict = {};
    payloadDict[toggleId] = toggleVal;
    var payload = JSON.stringify(payloadDict);
    sendPost(payload);
    setTimeout(function(){
        var currPage = window.location.pathname;
        window.location.replace(currPage);
        return false;
    }, 500);
}

// download page buttons
function rescanPending() {
    var payload = JSON.stringify({'rescan_pending': true});
    animate('rescan-icon', 'rotate-img');
    sendPost(payload);
    setTimeout(function(){
        checkMessages();
    }, 500);
}

function dlPending() {
    var payload = JSON.stringify({'dl_pending': true});
    animate('download-icon', 'bounce-img');
    sendPost(payload);
    setTimeout(function(){
        checkMessages();
    }, 500);
}

function toIgnore(button) {
    var youtube_id = button.getAttribute('data-id');
    var payload = JSON.stringify({'ignore': youtube_id});
    sendPost(payload);
    document.getElementById('dl-' + youtube_id).remove();
}

function downloadNow(button) {
    var youtube_id = button.getAttribute('data-id');
    var payload = JSON.stringify({'dlnow': youtube_id});
    sendPost(payload);
    document.getElementById(youtube_id).remove();
    setTimeout(function(){
        checkMessages();
    }, 500);
}

function forgetIgnore(button) {
    var youtube_id = button.getAttribute('data-id');
    var payload = JSON.stringify({'forgetIgnore': youtube_id});
    sendPost(payload);
    document.getElementById("dl-" + youtube_id).remove();
}

function addSingle(button) {
    var youtube_id = button.getAttribute('data-id');
    var payload = JSON.stringify({'addSingle': youtube_id});
    sendPost(payload);
    document.getElementById("dl-" + youtube_id).remove();
    setTimeout(function(){
        checkMessages();
    }, 500);
}

function deleteQueue(button) {
    var to_delete = button.getAttribute('data-id');
    var payload = JSON.stringify({'deleteQueue': to_delete});
    console.log(payload);
    sendPost(payload);
    setTimeout(function(){
        location.reload();
        return false;
    }, 1000);
}

function stopQueue() {
    var payload = JSON.stringify({'queue': 'stop'});
    sendPost(payload);
    document.getElementById('stop-icon').remove();
}

function killQueue() {
    var payload = JSON.stringify({'queue': 'kill'});
    sendPost(payload);
    document.getElementById('kill-icon').remove();
}

// settings page buttons
function manualImport() {
    var payload = JSON.stringify({'manual-import': true});
    sendPost(payload);
    // clear button
    var message = document.createElement('p');
    message.innerText = 'processing import';
    var toReplace = document.getElementById('manual-import');
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

function reEmbed() {
    var payload = JSON.stringify({'re-embed': true});
    sendPost(payload);
    // clear button
    var message = document.createElement('p');
    message.innerText = 'processing thumbnails';
    var toReplace = document.getElementById('re-embed');
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

function dbBackup() {
    var payload = JSON.stringify({'db-backup': true});
    sendPost(payload)
    // clear button
    var message = document.createElement('p');
    message.innerText = 'backing up archive';
    var toReplace = document.getElementById('db-backup');
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

function dbRestore(button) {
    var fileName = button.getAttribute("data-id");
    var payload = JSON.stringify({'db-restore': fileName});
    sendPost(payload);
    // clear backup row
    var message = document.createElement('p');
    message.innerText = 'restoring from backup';
    var toReplace = document.getElementById(fileName);
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

function fsRescan() {
    var payload = JSON.stringify({'fs-rescan': true});
    sendPost(payload);
    // clear button
    var message = document.createElement('p');
    message.innerText = 'File system scan in progress';
    var toReplace = document.getElementById('fs-rescan');
    toReplace.innerHTML = '';
    toReplace.appendChild(message);
}

function findPlaylists(button) {
    var channel_id = button.getAttribute("data-id");
    var payload = JSON.stringify({'find-playlists': channel_id});
    sendPost(payload);
    // clear button
    var message = document.createElement('p');
    message.innerText = 'Scraping for playlists in progress';
    document.getElementById("find-playlists-button").replaceWith(message);
    setTimeout(function(){
        checkMessages();
    }, 500);
}

// delete from file system
function deleteConfirm() {
    to_show = document.getElementById("delete-button");
    document.getElementById("delete-item").style.display = 'none';
    to_show.style.display = "block";
}

function deleteVideo(button) {
    var to_delete = button.getAttribute("data-id");
    var to_redirect = button.getAttribute("data-redirect");
    var payload = JSON.stringify({"delete-video": to_delete});
    sendPost(payload);
    setTimeout(function(){
        var redirect = "/channel/" + to_redirect;
        window.location.replace(redirect);
        return false;
    }, 1000);
}

function deleteChannel(button) {
    var to_delete = button.getAttribute("data-id");
    var payload = JSON.stringify({"delete-channel": to_delete});
    sendPost(payload);
    setTimeout(function(){
        window.location.replace("/channel/");
        return false;
    }, 1000);
}

function deletePlaylist(button) {
    var playlist_id = button.getAttribute("data-id");
    var playlist_action = button.getAttribute("data-action");
    var payload = JSON.stringify({
        "delete-playlist": {
            "playlist-id": playlist_id,
            "playlist-action": playlist_action
        }
    });
    console.log(payload);
    sendPost(payload);
    setTimeout(function(){
        window.location.replace("/playlist/");
        return false;
    }, 1000);
}

function cancelDelete() {
    document.getElementById("delete-button").style.display = 'none';
    document.getElementById("delete-item").style.display = 'block';
}

// player
function createPlayer(button) {
    var videoId = button.getAttribute('data-id');
    var videoPlayerData = getVideoPlayerData(videoId);
    var videoData = getVideoData(videoId);
    var channelData = getChannelData(videoPlayerData.channel_id);

    var videoUrl = videoPlayerData.media_url;
    var videoThumbUrl = videoPlayerData.vid_thumb_url;
    var videoName = videoPlayerData.title;
    var videoDescription = getFormattedDescription(videoData.description);

    var videoProgress = videoData.player.progress; // Groundwork for saving video position, change once progress variable is added to API
    var videoLastRefresh = formatDates(new Date(videoData.vid_last_refresh * 1000)); // Convert s to ms
    var videoPublished = formatDates(new Date(videoData.published + "T00:00:00")); // Time needed or else the date is always one day behind, UTC to local or something
    var videoViews = formatNumbers(videoData.stats.view_count);
    var videoLikeCount = formatNumbers(videoData.stats.like_count);
    var videoDislikeCount = formatNumbers(videoData.stats.dislike_count);
    var videoRating = videoData.stats.average_rating.toFixed(1);
    var videoStarRating = getStarRating(videoData.stats.average_rating);

    var channelId = videoPlayerData.channel_id;
    var channelName = videoPlayerData.channel_name;
    var channelSubs = formatNumbers(channelData.channel_subs);

    removePlayer();
    document.getElementById(videoId).outerHTML = ''; // Remove watch indicator from video info

    // If cast integration is enabled create cast button
    var castScript = document.getElementById('cast-script');
    if (typeof(castScript) != 'undefined' && castScript != null) {
        var castButton = `<google-cast-launcher id="castbutton"></google-cast-launcher>`
    } else {
        var castButton = ``
    };
    // Watched indicator
    if (videoPlayerData.is_watched) {
        var playerState = "seen";
        var watchedFunction = "Unwatched";
    } else {
        var playerState = "unseen";
        var watchedFunction = "Watched";  
    };
    // Channel Active
    if (channelData.channel_active) {
        var channelActive = `<a href="https://www.youtube.com/watch?v=${videoId}" target="_blank">Active</a>`
    } else {
        var channelActive = `Deactivated` 
    };
    const markup = `
    <div data-id="${videoId}">
        <div class="video-main">
            <video src="${videoUrl}" poster="${videoThumbUrl}" ontimeupdate="onVideoProgress('${videoId}')" onloadedmetadata="setVideoProgress(${videoProgress})" controls autoplay type='video/mp4' width="100%" playsinline id="video-item"></video>
        </div>
        <div class="player-title boxed-content">
            <img class="close-button" src="/static/img/icon-close.svg" alt="close-icon" data="${videoId}" onclick="removePlayer()" title="Close player">
            <img src="/static/img/icon-${playerState}.svg" alt="${playerState}-icon" id="${videoId}" onclick="is${watchedFunction}(this.id)" class="${playerState}-icon" title="Mark as ${watchedFunction}">
        </div>
        <div class="boxed-content">
            <div class="title-bar">
                ${castButton}
                <a href="/video/${videoId}/"><h1 id="video-title">${videoName}</h1></a>
            </div>
            <div class="info-box info-box-3">
                <div class="info-box-item">
                    <div class="round-img">
                        <a href="/channel/${channelId}/">
                            <img src="/cache/channels/${channelId}_thumb.jpg" alt="channel-thumb">
                        </a>
                    </div>
                    <div>
                        <h3><a href="/channel/${channelId}/">${channelName}</a></h3>
                        <p>Subscribers: ${channelSubs}</p> 
                    </div>
                </div>
                <div class="info-box-item">
                    <div>
                        <p>Published: ${videoPublished}</p>
                        <p>Last refreshed: ${videoLastRefresh}</p>
                        <p>Youtube: ${channelActive}</p>
                        <a download href="${videoUrl}"><button id="download-item">Download File</button></a>
                        <button onclick="deleteConfirm()" id="delete-item">Delete Video</button>
                        <div class="delete-confirm" id="delete-button">
                            <span>Are you sure? </span><button class="danger-button" onclick="deleteVideo(this)" data-id="${videoId}" data-redirect = "${channelId}">Delete</button> <button onclick="cancelDelete()">Cancel</button>
                        </div>
                    </div>
                </div>
                <div class="info-box-item">
                    <div>
                        <p>Views: ${videoViews}</p>
                        <p class="thumb-icon like"><img src="/static/img/icon-thumb.svg" alt="thumbs-up">: ${videoLikeCount}</p>
                        <p class="thumb-icon dislike"><img src="/static/img/icon-thumb.svg" alt="thumbs-down">: ${videoDislikeCount}</p>
                        <p class="rating-stars">Rating: ${videoStarRating} (${videoRating})</p>
                    </div>
                </div>
            </div>
            <!--<div class="info-box-item description-box">
                <p>Description: <button onclick="textReveal()" id="text-reveal-button">Show</button></p>
                <div id="text-reveal" class="description-text">
                    <p>${videoDescription}</p>
                </div>
            </div> -->
        </div>
    </div>
    `
    const divPlayer =  document.getElementById("player");
    divPlayer.innerHTML = markup;
}

// Set video progress in seconds
function setVideoProgress(videoProgress) {
    if (isNaN(videoProgress)) {
        videoProgress = 0;
    }
    var videoElement = document.getElementById("video-item");
    videoElement.currentTime = videoProgress;
}

// Runs on video playback, marks video as watched if video gets to 90% or higher, WIP sends position to api
function onVideoProgress(videoId) {
    var videoElement = document.getElementById("video-item");
    if ((videoElement.currentTime % 10).toFixed(1) <= 0.2) { // Check progress every 10 seconds or else progress is checked a few times a second
        // sendVideoProgress(videoId, videoElement.currentTime); // Groundwork for saving video position
        if ((videoElement.currentTime / videoElement.duration) >= 0.90) {
            isWatched(videoId);
        }
    }

}

// Groundwork for saving video position
function sendVideoProgress(videoId, videoProgress) {
    var apiEndpoint = "/api/video/" + videoId + "/";
    if (isNaN(videoProgress)) {
        videoProgress = 0;
    }
    progress = { 
        player: {
            progress: videoProgress 
        }
    };
    videoData = apiRequest(apiEndpoint, "POST", progress);
}

// Returns HTML formatted description
function getFormattedDescription(description) {
    return description.split('\n\n').join('</p><p>').split('\n').join('<br>');
}

// Returns HTML stars when given a rating
function getStarRating(rating) {
    var stars = '';
    for (let i = 1; i <= parseFloat(rating); i++) {
        stars = stars + '<img src="/static/img/icon-star-full.svg" alt="full">';
    }
    if ((parseFloat(rating) % 1) >= 0.5) {
        stars = stars + '<img src="/static/img/icon-star-full.svg" alt="full">';
    } else if ((parseFloat(rating) % 1) > 0) {
        stars = stars + '<img src="/static/img/icon-star-half.svg" alt="half">';
    }
    for (let i = 1; i <= (5 - parseFloat(rating)); i++) {
        stars = stars + '<img src="/static/img/icon-star-empty.svg" alt="empty">';
    }
    return stars;
}

// Format dates to match format in other locations
function formatDates(dateUnformatted) {
    // var dateFormatted = dateUnformatted.toLocaleString('en-US', { dateStyle: "medium" }); // en-US is simular but has the day and month switched and en-GB has correct order but no comma, so none of the huilt in formats worked directly 
    var dateFormatted = dateUnformatted.toLocaleString("en-US", { day: "2-digit" }) + " " +  dateUnformatted.toLocaleString("en-US", { month: "short" }) + ", " + dateUnformatted.toLocaleString("en-US", { year: "numeric" });
    console.log(dateFormatted);
    return dateFormatted;
}

// Format numbers for frontend
function formatNumbers(number) {
    var numberUnformatted = parseFloat(number);
    if (numberUnformatted > 999999999) {
        var numberFormatted = (numberUnformatted / 1000000000).toFixed(1).toString() + " billion";
    } else if (numberUnformatted > 999999) {
        var numberFormatted = (numberUnformatted / 1000000).toFixed(1).toString() + " million";
    } else if (numberUnformatted > 999) {
        var numberFormatted = numberUnformatted.toLocaleString("en-US");
    } else {
        var numberFormatted = numberUnformatted;
    }
    return numberFormatted;
}

// Gets video player data in JSON format when passed video ID
function getVideoPlayerData(videoId) {
    var apiEndpoint = "/api/video/" + videoId + "/player/";
    videoPlayerData = apiRequest(apiEndpoint, "GET");
    return videoPlayerData;
}

// Gets video data in JSON format when passed video ID
function getVideoData(videoId) {
    var apiEndpoint = "/api/video/" + videoId + "/";
    videoData = apiRequest(apiEndpoint, "GET");
    return videoData.data;
}

// Gets channel data in JSON format when passed channel ID
function getChannelData(channelId) {
    var apiEndpoint = "/api/channel/" + channelId + "/";
    channelData = apiRequest(apiEndpoint, "GET");
    return channelData.data;
}

// Gets playlist data in JSON format when passed playlist ID
function getPlaylistData(playlistId) {
    var apiEndpoint = "/api/playlist/" + playlistId + "/";
    playlistData = apiRequest(apiEndpoint, "GET");
    return playlistData.data;
}

// Makes api requests when passed an endpoint and method ("GET" or "POST")
function apiRequest(apiEndpoint, method, data) {
    const xhttp = new XMLHttpRequest();
    var sessionToken = getCookie("sessionid");
    xhttp.open(method, apiEndpoint, false);
    xhttp.setRequestHeader("Authorization", "Token " + sessionToken);
    xhttp.setRequestHeader("Content-Type", "application/json");
    xhttp.send(JSON.stringify(data));
    return JSON.parse(xhttp.responseText);
}

function removePlayer() {
    var playerElement = document.getElementById('player');
    if (playerElement.hasChildNodes()) {
        var youtubeId = playerElement.childNodes[1].getAttribute("data-id");
        var playedStatus = document.createDocumentFragment();
        var playedBox = document.getElementById(youtubeId);
        if (playedBox) {
            playedStatus.appendChild(playedBox);
        };
        playerElement.innerHTML = '';
        // append played status
        var videoInfo = document.getElementById('video-info-' + youtubeId);
        videoInfo.insertBefore(playedStatus, videoInfo.firstChild);
    };
}


// multi search form
function searchMulti(query) {
    if (query.length > 1) {
        var payload = JSON.stringify({'multi_search': query})
        var http = new XMLHttpRequest();
        http.onreadystatechange = function() {
            if (http.readyState === 4) {
                allResults = JSON.parse(http.response)['results'];
                populateMultiSearchResults(allResults);
            };
        };
        http.open("POST", "/process/", true);
        http.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        http.setRequestHeader("Content-type", "application/json");
        http.send(payload);
    };
}

function getViewDefaults(view) {
    var defaultView = document.getElementById("id_" + view).value;
    return defaultView
}

function populateMultiSearchResults(allResults) {
    // videos
    var defaultVideo = getViewDefaults("home");
    var allVideos = allResults["video_results"];
    var videoBox = document.getElementById("video-results");
    videoBox.innerHTML = "";
    for (let index = 0; index < allVideos.length; index++) {
        const video = allVideos[index]["source"];
        const videoDiv = createVideo(video, defaultVideo);
        videoBox.appendChild(videoDiv);
    };
    // channels
    var defaultChannel = getViewDefaults("channel");
    var allChannels = allResults["channel_results"];
    var channelBox = document.getElementById("channel-results");
    channelBox.innerHTML = "";
    for (let index = 0; index < allChannels.length; index++) {
        const channel = allChannels[index]["source"];
        const channelDiv = createChannel(channel, defaultChannel);
        channelBox.appendChild(channelDiv);
    };
    // playlists
    var defaultPlaylist = getViewDefaults("playlist");
    var allPlaylists = allResults["playlist_results"];
    var playlistBox = document.getElementById("playlist-results");
    playlistBox.innerHTML = "";
    for (let index = 0; index < allPlaylists.length; index++) {
        const playlist = allPlaylists[index]["source"];
        const playlistDiv = createPlaylist(playlist, defaultPlaylist);
        playlistBox.appendChild(playlistDiv);
    };
}


function createVideo(video, viewStyle) {
    // create video item div from template
    const videoId = video["youtube_id"];
    const videoData = getVideoData(videoId);
    const videoPlayerData = getVideoPlayerData(videoId);
    const thumbUrl = videoPlayerData.vid_thumb_url;
    const videoTitle = videoPlayerData.title;
    const videoPublished = formatDates(new Date(videoData.published + "T00:00:00"));
    const videoDuration = videoData.player.duration_str;
    if (videoPlayerData.is_watched) {
        var playerState = "seen";
    } else {
        var playerState = "unseen";
    };
    const channelId = videoPlayerData.channel_id;
    const channelName = videoPlayerData.channel_name;
    // build markup
    const markup = `
    <a href="#player" data-id="${videoId}" onclick="createPlayer(this)">
        <div class="video-thumb-wrap ${viewStyle}">
            <div class="video-thumb">
                <img src="${thumbUrl}" alt="video-thumb">
            </div>
            <div class="video-play">
                <img src="/static/img/icon-play.svg" alt="play-icon">
            </div>
        </div>
    </a>
    <div class="video-desc ${viewStyle}">
        <div class="video-desc-player" id="video-info-${videoId}">
                <img src="/static/img/icon-${playerState}.svg" alt="${playerState}-icon" id="${videoId}" onclick="isWatched(this.id)" class="${playerState}-icon">
            <span>${videoPublished} | ${videoDuration}</span>
        </div>
        <div>
            <a href="/channel/${channelId}/"><h3>${channelName}</h3></a>
            <a class="video-more" href="/video/${videoId}/"><h2>${videoTitle}</h2></a>
        </div>
    </div>
    `
    const videoDiv = document.createElement("div");
    videoDiv.setAttribute("class", "video-item " + viewStyle);
    videoDiv.innerHTML = markup;
    return videoDiv;
}


function createChannel(channel, viewStyle) {
    // create channel item div from template
    const channelId = channel["channel_id"];
    const channelData = getChannelData(channelId);
    const channelName = channelData.channel_name;
    const channelSubs = formatNumbers(channelData.channel_subs);
    const channelLastRefresh = formatDates(new Date(channelData.channel_last_refresh * 1000));
    if (channelData.channel_subscribed) {
        var button = `<button class="unsubscribe" type="button" id="${channelId}" onclick="unsubscribe(this.id)" title="Unsubscribe from ${channelName}">Unsubscribe</button>`
    } else {
        var button = `<button type="button" id="${channelId}" onclick="subscribe(this.id)" title="Subscribe to ${channelName}">Subscribe</button>`
    };
    // build markup
    const markup = `
    <div class="channel-banner ${viewStyle}">
        <a href="/channel/${channelId}/">
            <img src="/cache/channels/${channelId}_banner.jpg" alt="${channelId}-banner">
        </a>
    </div>
    <div class="info-box info-box-2 ${viewStyle}">
        <div class="info-box-item">
            <div class="round-img">
                <a href="/channel/${channelId}/">
                    <img src="/cache/channels/${channelId}_thumb.jpg" alt="channel-thumb">
                </a>
            </div>
            <div>
                <h3><a href="/channel/${channelId}/">${channelName}</a></h3>
                <p>Subscribers: ${channelSubs}</p>
            </div>
        </div>
        <div class="info-box-item">
            <div>
                <p>Last refreshed: ${channelLastRefresh}</p>
                ${button}
            </div>
        </div>
    </div>
    `
    const channelDiv = document.createElement("div");
    channelDiv.setAttribute("class", "channel-item " + viewStyle);
    channelDiv.innerHTML = markup;
    return channelDiv;
}

function createPlaylist(playlist, viewStyle) {
    // create playlist item div from template
    const playlistId = playlist["playlist_id"];
    const playlistData = getPlaylistData(playlistId);
    const playlistName = playlistData.playlist_name;
    const playlistChannelId = playlistData.playlist_channel_id;
    const playlistChannel = playlistData.playlist_channel;
    const playlistLastRefresh = formatDates(new Date(playlistData.playlist_last_refresh * 1000));
    if (playlistData.playlist_subscribed) {
        var button = `<button class="unsubscribe" type="button" id="${playlistId}" onclick="unsubscribe(this.id)" title="Unsubscribe from ${playlistName}">Unsubscribe</button>`
    } else {
        var button = `<button type="button" id="${playlistId}" onclick="subscribe(this.id)" title="Subscribe to ${playlistName}">Subscribe</button>`
    };
    const markup = `
    <div class="playlist-thumbnail">
        <a href="/playlist/${playlistId}/">
            <img src="/cache/playlists/${playlistId}.jpg" alt="${playlistId}-thumbnail">
        </a>
    </div>
    <div class="playlist-desc ${viewStyle}">
        <a href="/channel/${playlistChannelId}/"><h3>${playlistChannel}</h3></a>
        <a href="/playlist/${playlistId}/"><h2>${playlistName}</h2></a>
        <p>Last refreshed: ${playlistLastRefresh}</p>
        ${button}
    </div>
    `
    const playlistDiv = document.createElement("div");
    playlistDiv.setAttribute("class", "playlist-item " + viewStyle);
    playlistDiv.innerHTML = markup;
    return playlistDiv;
}


// generic
function sendPost(payload) {
    var http = new XMLHttpRequest();
    http.open("POST", "/process/", true);
    http.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
    http.setRequestHeader("Content-type", "application/json");
    http.send(payload);
}


function getCookie(c_name) {
    if (document.cookie.length > 0) {
        c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) c_end = document.cookie.length;
            return unescape(document.cookie.substring(c_start,c_end));
        };
    };
    return "";
}


// animations
function textReveal() {
    var textBox = document.getElementById('text-reveal');
    var button = document.getElementById('text-reveal-button');
    var textBoxHeight = textBox.style.height;
    if (textBoxHeight === 'unset') {
        textBox.style.height = '0px';
        button.innerText = 'Show';
    } else {
        textBox.style.height = 'unset';
        button.innerText = 'Hide';
    };
}

function showForm() {
    var formElement = document.getElementById('hidden-form');
    var displayStyle = formElement.style.display
    if (displayStyle === "") {
        formElement.style.display = 'block';
    } else {
        formElement.style.display = "";
    };
    animate('animate-icon', 'pulse-img');
}

function animate(elementId, animationClass) {
    var toAnimate = document.getElementById(elementId);
    if (toAnimate.className !== animationClass) {
        toAnimate.className = animationClass;
    } else {
        toAnimate.classList.remove(animationClass);
    };
}

