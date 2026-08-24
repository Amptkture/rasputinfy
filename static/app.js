const POLL_MS = 2000;

const playingView = document.getElementById("playing-view");
const standbyView = document.getElementById("standby-view");
const artistEl = document.getElementById("artist");
const titleEl = document.getElementById("title");

let lastPayload = "";

function showPlaying(payload) {
  playingView.classList.remove("hidden", "paused");
  standbyView.classList.add("hidden");
  playingView.setAttribute("aria-hidden", "false");
  standbyView.setAttribute("aria-hidden", "true");

  artistEl.textContent = payload.artist || "Unknown Artist";
  titleEl.textContent = payload.title || "Unknown Track";

  if (payload.status === "paused") {
    playingView.classList.add("paused");
  }
}

function showStandby() {
  playingView.classList.add("hidden");
  standbyView.classList.remove("hidden");
  playingView.setAttribute("aria-hidden", "true");
  standbyView.setAttribute("aria-hidden", "false");
}

function isActivePlayback(status) {
  return status === "playing" || status === "paused";
}

async function pollNowPlaying() {
  try {
    const response = await fetch("/api/now-playing", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const payload = await response.json();
    const serialized = JSON.stringify(payload);
    if (serialized !== lastPayload) {
      lastPayload = serialized;
      if (isActivePlayback(payload.status) && payload.title) {
        showPlaying(payload);
      } else {
        showStandby();
      }
    }
  } catch (_error) {
    showStandby();
  }
}

pollNowPlaying();
setInterval(pollNowPlaying, POLL_MS);
