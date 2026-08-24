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

  window.dispatchEvent(new Event("resize"));
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
startHorizonGrid();

function startHorizonGrid() {
  const canvas = document.getElementById("grid-floor");
  if (!canvas || !canvas.getContext) {
    return;
  }

  const ctx = canvas.getContext("2d");
  const zNear = 1;
  const zFar = 16;
  const rowSpacing = 0.48;
  const colSpacing = 0.62;
  const xExtent = 10;
  const scrollSpeed = 1.15;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (width < 2 || height < 2) {
      return;
    }
    const nextW = Math.round(width * dpr);
    const nextH = Math.round(height * dpr);
    if (canvas.width !== nextW || canvas.height !== nextH) {
      canvas.width = nextW;
      canvas.height = nextH;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
  }

  function vanishingPoint(width, height) {
    const canvasRect = canvas.getBoundingClientRect();
    const sun = document.querySelector(".sun");
    const mountains = document.querySelector(".mountains");
    let x = width / 2;
    if (sun) {
      const sunRect = sun.getBoundingClientRect();
      x = sunRect.left + sunRect.width / 2 - canvasRect.left;
    }
    const y = mountains
      ? mountains.getBoundingClientRect().bottom - canvasRect.top
      : height * (1 - 0.32);
    return { x, y };
  }

  function draw(now) {
    resize();
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    ctx.clearRect(0, 0, width, height);

    if (!playingView.classList.contains("hidden")) {
      const { x: vpX, y: vpY } = vanishingPoint(width, height);
      const groundH = height - vpY;

      if (groundH > 8) {
        const scale = (width * 1.15 * zNear) / xExtent;
        const lineWidth = Math.max(2.5, width / 420);
        const offset = ((now / 1000) * scrollSpeed) % rowSpacing;

        ctx.save();
        ctx.beginPath();
        ctx.rect(0, vpY, width, groundH);
        ctx.clip();
        ctx.lineCap = "butt";

        ctx.beginPath();
        for (let x = -xExtent; x <= xExtent + 0.001; x += colSpacing) {
          const xBottom = vpX + (x * scale) / zNear;
          ctx.moveTo(xBottom, height);
          ctx.lineTo(vpX, vpY);
        }
        ctx.strokeStyle = "rgba(255, 42, 109, 0.95)";
        ctx.lineWidth = lineWidth;
        ctx.stroke();

        for (let z = zNear + offset; z < zFar; z += rowSpacing) {
          const depth = (z - zNear) / (zFar - zNear);
          const y = vpY + groundH * (zNear / z);
          const half = (xExtent * scale) / z;
          const alpha = 0.95 * (1 - depth * depth * 0.85);

          ctx.beginPath();
          ctx.moveTo(vpX - half, y);
          ctx.lineTo(vpX + half, y);
          ctx.strokeStyle = `rgba(5, 217, 232, ${alpha.toFixed(3)})`;
          ctx.lineWidth = lineWidth;
          ctx.stroke();
        }

        ctx.restore();
      }
    }

    requestAnimationFrame(draw);
  }

  resize();
  window.addEventListener("resize", resize);
  requestAnimationFrame(draw);
}
