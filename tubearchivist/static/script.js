
function sortChange(sortValue) {
    var payload = JSON.stringify({'sort_order': sortValue});
    sendPost(payload);
    setTimeout(function(){
        location.reload();
        return false;
    }, 500);
}

function isWatched(youtube_id) {
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
    var mediaUrl = button.getAttribute('data-src');
    var mediaThumb = button.getAttribute('data-thumb');
    var mediaTitle = button.getAttribute('data-title');
    var mediaChannel = button.getAttribute('data-channel');
    var mediaChannelId = button.getAttribute('data-channel-id');
    var dataId = button.getAttribute('data-id');
    // get watched status
    var playedStatus = document.createDocumentFragment();
    playedStatus.appendChild(document.getElementById(dataId));
    // create player
    removePlayer();
    var playerElement = document.createElement('div');
    playerElement.classList.add("video-player");
    // var playerElement = document.getElementById('player');
    playerElement.setAttribute('data-id', dataId);
    // playerElement.innerHTML = '';
    var videoPlayer = document.createElement('video');
    videoPlayer.setAttribute('src', mediaUrl);
    videoPlayer.setAttribute('controls', true);
    videoPlayer.setAttribute('autoplay', true);
    videoPlayer.setAttribute('width', '100%');
    videoPlayer.setAttribute('playsinline', true);
    videoPlayer.setAttribute('poster', mediaThumb);
    playerElement.appendChild(videoPlayer);
    // title bar
    var titleBar = document.createElement('div');
    titleBar.classList.add('player-title', 'boxed-content');
    // close
    var closeButton = document.createElement('img');
    closeButton.className = 'close-button';
    closeButton.setAttribute('src', "/static/img/icon-close.svg");
    closeButton.setAttribute('alt', 'close-icon');
    closeButton.setAttribute('data', dataId);
    closeButton.setAttribute('onclick', "removePlayer()");
    closeButton.setAttribute('title', 'Close player');
    titleBar.appendChild(closeButton);
    // played
    titleBar.appendChild(playedStatus);
    // channel title
    var channelTitleLink = document.createElement('a');
    channelTitleLink.setAttribute('href', '/channel/' + mediaChannelId + '/');
    var channelTitle = document.createElement('h3');
    channelTitle.innerText = mediaChannel;
    channelTitleLink.appendChild(channelTitle);
    titleBar.appendChild(channelTitleLink);
    // video title
    var videoTitleLink = document.createElement('a');
    videoTitleLink.setAttribute('href', '/video/' + dataId + '/');
    var videoTitle = document.createElement('h2');
    videoTitle.innerText = mediaTitle;
    videoTitleLink.appendChild(videoTitle);
    titleBar.appendChild(videoTitleLink);
    // add titlebar
    playerElement.appendChild(titleBar);
    // add whole
    document.getElementById("player").appendChild(playerElement);
}

function removePlayer() {
    var playerElement = document.getElementById('player');
    if (playerElement.hasChildNodes()) {
        var youtubeId = playerElement.childNodes[0].getAttribute("data-id");
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


function populateMultiSearchResults(allResults) {
    // videos
    var allVideos = allResults["video_results"];
    var videoBox = document.getElementById("video-results");
    videoBox.innerHTML = "";
    for (let index = 0; index < allVideos.length; index++) {
        const video = allVideos[index]["source"];
        const videoDiv = createVideo(video, "grid");
        videoBox.appendChild(videoDiv);
    };
    // channels
    var allChannels = allResults["channel_results"];
    var channelBox = document.getElementById("channel-results");
    channelBox.innerHTML = "";
    for (let index = 0; index < allChannels.length; index++) {
        const channel = allChannels[index]["source"];
        const channelDiv = createChannel(channel, "list");
        channelBox.appendChild(channelDiv);
    };
    // playlists
    var allPlaylists = allResults["playlist_results"];
    var playlistBox = document.getElementById("playlist-results");
    playlistBox.innerHTML = "";
    for (let index = 0; index < allPlaylists.length; index++) {
        const playlist = allPlaylists[index]["source"];
        const playlistDiv = createPlaylist(playlist, "grid");
        playlistBox.appendChild(playlistDiv);
    };
}


function createVideo(video, viewStyle) {
    // create video item div from template
    const videoId = video["youtube_id"];
    const mediaUrl = video["media_url"];
    const thumbUrl = "/cache/" + video["vid_thumb_url"];
    const videoTitle = video["title"];
    const videoPublished = video["published"];
    const videoDuration = video["player"]["duration_str"];
    if (video["player"]["watched"]) {
        var playerState = "seen";
    } else {
        var playerState = "unseen";
    };
    const channelId = video["channel"]["channel_id"];
    const channelName = video["channel"]["channel_name"];
    // build markup
    const markup = `
    <a href="#player" data-src="/media/${mediaUrl}" data-thumb="${thumbUrl}" data-title="${videoTitle}" data-channel="${channelName}" data-channel-id="${channelId}" data-id="${videoId}" onclick="createPlayer(this)">
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
    videoDiv.innerHTML = markup
    return videoDiv
}


function createChannel(channel, viewStyle) {
    // create channel item div from template
    const channelId = channel["channel_id"];
    const channelName = channel["channel_name"];
    const channelSubs = channel["channel_subs"];
    const channelLastRefresh = channel["channel_last_refresh"];
    if (channel["channel_subscribed"]) {
        var button = `<button class="unsubscribe" type="button" id="${channelId}" onclick="unsubscribe(this.id)" title="Unsubscribe from ${channelName}">Unsubscribe</button>`
    } else {
        var button = `<button type="button" id="${channelId}" onclick="subscribe(this.id)" title="Subscribe to ${channelName}">Subscribe</button>`
    };
    // build markup
    const markup = `
    <div class="channel-banner list">
        <a href="/channel/${channelId}/">
            <img src="/cache/channels/${channelId}_banner.jpg" alt="${channelId}-banner">
        </a>
    </div>
    <div class="info-box info-box-2 list">
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
    return channelDiv
}

function createPlaylist(playlist, viewStyle) {
    // create playlist item div from template
    const playlistId = playlist["playlist_id"];
    const playlistName = playlist["playlist_name"];
    const playlistChannelId = playlist["playlist_channel_id"];
    const playlistChannel = playlist["playlist_channel"];
    const playlistLastRefresh = playlist["playlist_last_refresh"];
    if (playlist["playlist_subscribed"]) {
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
    return playlistDiv
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
        animate('add-icon', 'pulse-img');
    } else {
        formElement.style.display = "";
    }
}

function animate(elementId, animationClass) {
    var toAnimate = document.getElementById(elementId);
    if (toAnimate.className !== animationClass) {
        toAnimate.className = animationClass;
    }
}
