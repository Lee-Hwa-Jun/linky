const appRoot = document.querySelector("[data-lotto-app]");
const canvas = document.querySelector("#lotto-canvas");
const ctx = canvas.getContext("2d");

const drawButton = document.querySelector("#draw-btn");
const drawAllButton = document.querySelector("#draw-all-btn");
const resetButton = document.querySelector("#reset-btn");
const mainNumbersEl = document.querySelector("#main-numbers");
const saveStatusEl = document.querySelector("#save-status");

const profileLinksUrl = appRoot?.dataset.profileLinksUrl || "";
const ticketSubmitUrl = appRoot?.dataset.submitUrl || "";
const autoLinkConsumedOnLoad = appRoot?.dataset.autoLinkConsumed === "true";

const WIDTH = canvas.width;
const HEIGHT = canvas.height;
const FIXED_DT = 1 / 60;

const machine = {
  globe: { x: 406, y: 286, r: 176 },
  chuteStart: { x: 544, y: 414 },
  chuteMid: { x: 702, y: 476 },
  chuteEnd: { x: 834, y: 536 },
  trayRest: { x: 782, y: 532 },
  trayShadow: { x: 792, y: 554 },
};

const ballPalettes = [
  ["#ffd84d", "#ff9800"],
  ["#58b8ff", "#0b62e3"],
  ["#ff757f", "#db244d"],
  ["#9a8cff", "#5649dd"],
  ["#63df8d", "#15984f"],
];

const state = {
  balls: [],
  availableNumbers: [],
  drawnNumbers: [],
  mode: "idle",
  drawPhase: null,
  selectedBall: null,
  displayBall: null,
  elapsedInPhase: 0,
  sparkleTime: 0,
  trayPulse: 0,
  autoDrawPending: 0,
  autoDrawDelay: 0,
  clock: 0,
  lastTimestamp: 0,
  currentTicketPersisted: false,
  autoLinkConsumed: autoLinkConsumedOnLoad,
  adLinkUrl: null,
  adLinkRequest: null,
};

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function randRange(min, max) {
  return min + Math.random() * (max - min);
}

function paletteForNumber(number) {
  return ballPalettes[(number - 1) % ballPalettes.length];
}

function colorForSlot(number) {
  const [start, end] = paletteForNumber(number);
  return `linear-gradient(180deg, ${start}, ${end})`;
}

function setSaveStatus(message, tone = "") {
  if (!saveStatusEl) {
    return;
  }

  saveStatusEl.textContent = message;
  saveStatusEl.classList.remove("is-success", "is-error");
  if (tone) {
    saveStatusEl.classList.add(`is-${tone}`);
  }
}

function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(`${name}=`)) {
      return decodeURIComponent(trimmed.slice(name.length + 1));
    }
  }
  return "";
}

async function preloadAdLink() {
  if (state.autoLinkConsumed || !profileLinksUrl) {
    return null;
  }

  if (state.adLinkUrl) {
    return state.adLinkUrl;
  }

  if (!state.adLinkRequest) {
    state.adLinkRequest = fetch(profileLinksUrl, { credentials: "same-origin" })
      .then((response) => {
        if (!response.ok) {
          throw new Error("링크 API 호출 실패");
        }
        return response.json();
      })
      .then((data) => {
        state.adLinkUrl = data.links || null;
        return state.adLinkUrl;
      })
      .catch((error) => {
        console.error(error);
        return null;
      })
      .finally(() => {
        state.adLinkRequest = null;
      });
  }

  return state.adLinkRequest;
}

async function openAdLinkAfterCompletion(shouldOpenAdLink) {
  if (!shouldOpenAdLink) {
    return;
  }

  const adLinkUrl = state.adLinkUrl || (await preloadAdLink());
  if (!adLinkUrl) {
    return;
  }

  window.open(adLinkUrl, "_blank", "noopener");
}

async function submitCompletedTicket(numbers) {
  const response = await fetch(ticketSubmitUrl, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    body: JSON.stringify({ numbers }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "추첨 번호 저장 실패");
  }

  return payload;
}

async function finalizeCompletedTicket() {
  if (state.currentTicketPersisted || state.drawnNumbers.length !== 6) {
    return;
  }

  state.currentTicketPersisted = true;
  const shouldOpenAdLink = !state.autoLinkConsumed;

  try {
    setSaveStatus("추첨 번호를 저장하는 중입니다.");
    const payload = await submitCompletedTicket(state.drawnNumbers);
    state.autoLinkConsumed = true;
    setSaveStatus(
      `${payload.draw_round}회 / ${payload.draw_date} 추첨으로 저장되었습니다.`,
      "success"
    );
    await openAdLinkAfterCompletion(shouldOpenAdLink);
  } catch (error) {
    state.currentTicketPersisted = false;
    setSaveStatus(error.message || "추첨 번호 저장에 실패했습니다.", "error");
  }
}

function makeBall(number) {
  const { globe } = machine;
  const angle = Math.random() * Math.PI * 2;
  const radius = Math.sqrt(Math.random()) * (globe.r - 34);
  return {
    number,
    x: globe.x + Math.cos(angle) * radius,
    y: globe.y + Math.sin(angle) * radius,
    vx: randRange(-50, 50),
    vy: randRange(-30, 30),
    size: 18,
    rotation: Math.random() * Math.PI * 2,
    spin: randRange(-4, 4),
    turbulence: randRange(0, Math.PI * 2),
  };
}

function totalDrawnCount() {
  return state.drawnNumbers.length;
}

function syncControls() {
  const completed = totalDrawnCount() >= 6;
  const busy = state.mode === "drawing" || state.autoDrawPending > 0;
  drawButton.disabled = busy || completed;
  drawAllButton.disabled = busy || completed;
}

function renderResultBoard() {
  mainNumbersEl.innerHTML = "";
  state.drawnNumbers.forEach((number) => {
    const ball = document.createElement("span");
    ball.className = "number-ball";
    ball.textContent = String(number);
    ball.style.background = colorForSlot(number);
    mainNumbersEl.appendChild(ball);
  });
}

function resetGame() {
  state.availableNumbers = Array.from({ length: 45 }, (_, index) => index + 1);
  state.balls = state.availableNumbers.map((number) => makeBall(number));
  state.drawnNumbers = [];
  state.mode = "idle";
  state.drawPhase = null;
  state.selectedBall = null;
  state.displayBall = null;
  state.elapsedInPhase = 0;
  state.sparkleTime = 0;
  state.trayPulse = 0;
  state.autoDrawPending = 0;
  state.autoDrawDelay = 0;
  state.clock = 0;
  state.currentTicketPersisted = false;
  renderResultBoard();
  syncControls();
  setSaveStatus("6개 번호가 완성되면 해당 회차와 추첨일로 자동 저장됩니다.");
}

function popRandomNumber() {
  const index = Math.floor(Math.random() * state.availableNumbers.length);
  const [number] = state.availableNumbers.splice(index, 1);
  return number;
}

function beginDraw() {
  if (state.mode === "drawing" || totalDrawnCount() >= 6 || state.availableNumbers.length === 0) {
    return false;
  }

  const number = popRandomNumber();
  const index = state.balls.findIndex((ball) => ball.number === number);
  const pickedBall = state.balls.splice(index, 1)[0] || makeBall(number);

  state.mode = "drawing";
  state.drawPhase = "mixing";
  state.elapsedInPhase = 0;
  state.selectedBall = {
    ...pickedBall,
    bob: 0,
  };
  state.trayPulse = 0;
  syncControls();
  return true;
}

function queueAutoDrawAll() {
  if (state.mode === "drawing" || state.autoDrawPending > 0) {
    return;
  }

  const remaining = 6 - totalDrawnCount();
  if (remaining <= 0) {
    return;
  }

  state.autoDrawPending = remaining;
  state.autoDrawDelay = 0;
  syncControls();
}

function triggerAutoDrawStep() {
  if (state.mode === "drawing" || state.autoDrawPending <= 0 || totalDrawnCount() >= 6) {
    return;
  }

  if (beginDraw()) {
    state.autoDrawPending -= 1;
  }
}

function finishDraw() {
  if (!state.selectedBall) {
    return;
  }

  state.drawnNumbers.push(state.selectedBall.number);

  state.displayBall = {
    ...state.selectedBall,
    x: machine.trayRest.x,
    y: machine.trayRest.y,
    vx: 0,
    vy: 0,
    bob: 0,
    rotation: 0.24,
  };
  state.mode = "idle";
  state.drawPhase = null;
  state.selectedBall = null;
  state.elapsedInPhase = 0;
  state.sparkleTime = 1.2;
  state.trayPulse = 1;
  state.autoDrawDelay = state.autoDrawPending > 0 ? 0.42 : 0;
  renderResultBoard();
  syncControls();

  if (state.drawnNumbers.length === 6) {
    void finalizeCompletedTicket();
  }
}

function updateBallMotion(dt, ball, boost = 1) {
  const { globe } = machine;
  const relX = ball.x - globe.x;
  const relY = ball.y - globe.y;
  const distance = Math.hypot(relX, relY) || 1;
  const lowerZone = clamp((ball.y - (globe.y - 18)) / (globe.r + 22), 0, 1);
  const centerBias = 1 - clamp(Math.abs(relX) / (globe.r - ball.size), 0, 1);
  const blower = lowerZone * lowerZone * centerBias;
  const sideTurbulence =
    Math.sin(state.clock * 3 + ball.turbulence + ball.number * 0.3) * 220 * lowerZone +
    Math.cos(state.clock * 1.7 + ball.number) * 90 * blower;

  ball.vy += 820 * dt;
  ball.vy -= (880 + boost * 980) * blower * dt;
  ball.vx += sideTurbulence * dt;
  ball.vx += (-relX / globe.r) * 180 * lowerZone * dt;
  ball.vx *= 0.996;
  ball.vy *= 0.997;

  ball.x += ball.vx * dt;
  ball.y += ball.vy * dt;
  ball.rotation += (ball.spin + ball.vx * 0.005) * dt;

  const nextRelX = ball.x - globe.x;
  const nextRelY = ball.y - globe.y;
  const nextDistance = Math.hypot(nextRelX, nextRelY) || 1;
  const limit = globe.r - ball.size - 7;

  if (nextDistance > limit) {
    const nx = nextRelX / nextDistance;
    const ny = nextRelY / nextDistance;
    ball.x = globe.x + nx * limit;
    ball.y = globe.y + ny * limit;

    const velocityDot = ball.vx * nx + ball.vy * ny;
    ball.vx -= 1.9 * velocityDot * nx;
    ball.vy -= 1.9 * velocityDot * ny;

    if (ny > 0.55) {
      ball.vy -= 90 + boost * 70;
    }

    ball.vx *= 0.93;
    ball.vy *= 0.93;
  }
}

function lerpPoint(start, end, t) {
  return {
    x: start.x + (end.x - start.x) * t,
    y: start.y + (end.y - start.y) * t,
  };
}

function pointOnDrawPath(progress) {
  if (progress < 0.25) {
    const t = progress / 0.25;
    return lerpPoint(
      { x: machine.globe.x + 18, y: machine.globe.y + 112 },
      machine.chuteStart,
      t
    );
  }

  if (progress < 0.82) {
    const t = (progress - 0.25) / 0.57;
    const first = lerpPoint(machine.chuteStart, machine.chuteMid, t);
    const second = lerpPoint(machine.chuteMid, machine.chuteEnd, clamp((t - 0.18) / 0.82, 0, 1));
    return {
      x: first.x + (second.x - first.x) * t,
      y: first.y + (second.y - first.y) * t - Math.sin(t * Math.PI) * 12,
    };
  }

  const t = (progress - 0.82) / 0.18;
  return {
    x: machine.chuteEnd.x - t * 52,
    y: machine.chuteEnd.y - Math.sin(t * Math.PI) * 10,
  };
}

function updateSelectedBall(dt) {
  if (!state.selectedBall) {
    return;
  }

  if (state.drawPhase === "mixing") {
    updateBallMotion(dt, state.selectedBall, 2.5);
    state.selectedBall.bob = 0;
    if (state.elapsedInPhase >= 0.9) {
      state.drawPhase = "launch";
      state.elapsedInPhase = 0;
    }
    return;
  }

  if (state.drawPhase === "launch") {
    const progress = clamp(state.elapsedInPhase / 1.15, 0, 1);
    const point = pointOnDrawPath(progress);
    state.selectedBall.x = point.x;
    state.selectedBall.y = point.y;
    state.selectedBall.rotation += dt * 10;
    state.selectedBall.bob = Math.sin(progress * Math.PI * 8) * (1 - progress) * 0.45;

    if (progress >= 1) {
      state.drawPhase = "settle";
      state.elapsedInPhase = 0;
      state.selectedBall.x = machine.chuteEnd.x - 52;
      state.selectedBall.y = machine.chuteEnd.y;
      state.selectedBall.vx = -140;
      state.selectedBall.vy = 0;
      state.selectedBall.rotation = 0.2;
    }
    return;
  }

  if (state.drawPhase === "settle") {
    const progress = clamp(state.elapsedInPhase / 0.48, 0, 1);
    state.selectedBall.x += state.selectedBall.vx * dt;
    state.selectedBall.y = machine.chuteEnd.y + Math.sin(progress * Math.PI) * 2;
    state.selectedBall.rotation += dt * 8;

    if (progress >= 1) {
      finishDraw();
    }
  }
}

function update(dt) {
  state.clock += dt;
  state.sparkleTime = Math.max(0, state.sparkleTime - dt);
  state.trayPulse = Math.max(0, state.trayPulse - dt * 1.8);

  const boost = state.mode === "drawing" ? 1.35 : 0.95;
  state.balls.forEach((ball) => updateBallMotion(dt, ball, boost));

  if (state.mode === "drawing") {
    state.elapsedInPhase += dt;
    updateSelectedBall(dt);
    return;
  }

  if (state.autoDrawPending > 0) {
    state.autoDrawDelay = Math.max(0, state.autoDrawDelay - dt);
    if (state.autoDrawDelay === 0) {
      triggerAutoDrawStep();
    }
  }
}

function drawBackground() {
  const bg = ctx.createLinearGradient(0, 0, 0, HEIGHT);
  bg.addColorStop(0, "#f5e6fc");
  bg.addColorStop(0.42, "#ebf4ff");
  bg.addColorStop(1, "#d6ecfb");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);

  ctx.fillStyle = "rgba(255,255,255,0.45)";
  ctx.beginPath();
  ctx.ellipse(130, 100, 170, 84, 0.2, 0, Math.PI * 2);
  ctx.fill();
  ctx.beginPath();
  ctx.ellipse(794, 122, 230, 108, -0.32, 0, Math.PI * 2);
  ctx.fill();

  const floor = ctx.createLinearGradient(0, HEIGHT * 0.72, 0, HEIGHT);
  floor.addColorStop(0, "rgba(127, 154, 204, 0)");
  floor.addColorStop(1, "rgba(71, 106, 182, 0.22)");
  ctx.fillStyle = floor;
  ctx.fillRect(0, HEIGHT * 0.72, WIDTH, HEIGHT * 0.28);

  ctx.fillStyle = "rgba(92, 123, 184, 0.16)";
  ctx.beginPath();
  ctx.ellipse(440, 645, 324, 48, 0, 0, Math.PI * 2);
  ctx.fill();
}

function drawMachineFrame() {
  ctx.save();

  const sideFrame = ctx.createLinearGradient(0, 148, 0, 590);
  sideFrame.addColorStop(0, "rgba(255,255,255,0.88)");
  sideFrame.addColorStop(1, "rgba(170, 191, 233, 0.8)");
  ctx.strokeStyle = sideFrame;
  ctx.lineWidth = 9;
  ctx.beginPath();
  ctx.moveTo(238, 178);
  ctx.lineTo(238, 576);
  ctx.moveTo(594, 166);
  ctx.lineTo(594, 566);
  ctx.stroke();

  ctx.strokeStyle = "rgba(255,255,255,0.62)";
  ctx.lineWidth = 4;
  ctx.beginPath();
  ctx.moveTo(220, 194);
  ctx.quadraticCurveTo(406, 58, 616, 188);
  ctx.stroke();

  const body = ctx.createLinearGradient(0, 564, 0, 678);
  body.addColorStop(0, "#2459dd");
  body.addColorStop(0.55, "#0f37a8");
  body.addColorStop(1, "#0a2675");
  ctx.fillStyle = body;
  ctx.beginPath();
  ctx.ellipse(416, 620, 274, 72, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(255,255,255,0.16)";
  ctx.beginPath();
  ctx.ellipse(394, 590, 190, 26, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#173980";
  ctx.beginPath();
  ctx.roundRect(332, 522, 162, 42, 24);
  ctx.fill();

  ctx.fillStyle = "rgba(255,255,255,0.2)";
  ctx.beginPath();
  ctx.roundRect(356, 532, 114, 12, 6);
  ctx.fill();

  ctx.strokeStyle = "rgba(195, 217, 255, 0.95)";
  ctx.lineWidth = 18;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(machine.chuteStart.x, machine.chuteStart.y);
  ctx.quadraticCurveTo(666, 472, machine.chuteEnd.x, machine.chuteEnd.y);
  ctx.stroke();

  ctx.strokeStyle = "rgba(255,255,255,0.96)";
  ctx.lineWidth = 9;
  ctx.beginPath();
  ctx.moveTo(machine.chuteStart.x, machine.chuteStart.y);
  ctx.quadraticCurveTo(666, 472, machine.chuteEnd.x, machine.chuteEnd.y);
  ctx.stroke();

  const tray = ctx.createLinearGradient(720, 506, 720, 570);
  tray.addColorStop(0, "rgba(221, 236, 255, 0.86)");
  tray.addColorStop(1, "rgba(131, 160, 224, 0.92)");
  ctx.fillStyle = tray;
  ctx.beginPath();
  ctx.roundRect(714, 504, 184, 56, 24);
  ctx.fill();

  ctx.strokeStyle = "rgba(255,255,255,0.96)";
  ctx.lineWidth = 4;
  ctx.stroke();

  ctx.fillStyle = "rgba(255,255,255,0.24)";
  ctx.fillRect(732, 520, 142, 9);
  ctx.fillRect(732, 536, 112, 6);

  ctx.strokeStyle = "rgba(188, 212, 255, 0.72)";
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.moveTo(620, 430);
  ctx.lineTo(714, 510);
  ctx.stroke();

  ctx.restore();
}

function drawGlassGlobe() {
  const { globe } = machine;
  ctx.save();

  const shell = ctx.createRadialGradient(globe.x - 56, globe.y - 66, 24, globe.x, globe.y, globe.r);
  shell.addColorStop(0, "rgba(255,255,255,0.72)");
  shell.addColorStop(0.42, "rgba(255,255,255,0.18)");
  shell.addColorStop(1, "rgba(255,255,255,0.05)");
  ctx.fillStyle = shell;
  ctx.beginPath();
  ctx.arc(globe.x, globe.y, globe.r, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = "rgba(255,255,255,0.98)";
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.arc(globe.x, globe.y, globe.r, 0, Math.PI * 2);
  ctx.stroke();

  ctx.strokeStyle = "rgba(193, 216, 255, 0.78)";
  ctx.lineWidth = 2.5;
  ctx.beginPath();
  ctx.arc(globe.x, globe.y, globe.r - 17, 0.2, Math.PI * 1.92);
  ctx.stroke();

  ctx.beginPath();
  ctx.ellipse(globe.x - 56, globe.y - 72, 42, 108, 0.16, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(255,255,255,0.44)";
  ctx.stroke();

  ctx.beginPath();
  ctx.ellipse(globe.x + 34, globe.y + 18, globe.r - 70, globe.r - 106, 0.12, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(255,255,255,0.14)";
  ctx.stroke();

  ctx.restore();
}

function drawBall(ball, emphasis = 0) {
  const [start, end] = paletteForNumber(ball.number);
  const radius = ball.size + emphasis;
  const gradient = ctx.createLinearGradient(-radius, -radius, radius, radius);
  gradient.addColorStop(0, start);
  gradient.addColorStop(1, end);

  ctx.save();
  ctx.translate(ball.x, ball.y + (ball.bob || 0) * 8);
  ctx.rotate(ball.rotation);

  ctx.fillStyle = "rgba(14, 22, 46, 0.14)";
  ctx.beginPath();
  ctx.ellipse(2, radius * 0.88, radius * 0.88, radius * 0.34, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(255,255,255,0.34)";
  ctx.beginPath();
  ctx.arc(-radius * 0.32, -radius * 0.35, radius * 0.34, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "rgba(255,255,255,0.12)";
  ctx.beginPath();
  ctx.arc(radius * 0.16, radius * 0.2, radius * 0.72, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#ffffff";
  ctx.font = `800 ${Math.round(radius * 0.94)}px SUIT`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(String(ball.number), 0, 1);
  ctx.restore();
}

function drawGlobeBalls() {
  ctx.save();
  ctx.beginPath();
  ctx.arc(machine.globe.x, machine.globe.y, machine.globe.r - 8, 0, Math.PI * 2);
  ctx.clip();

  state.balls.forEach((ball) => drawBall(ball));
  if (state.selectedBall && state.drawPhase === "mixing") {
    drawBall(state.selectedBall, 1);
  }
  ctx.restore();
}

function drawTrayBall() {
  if (state.displayBall) {
    ctx.save();
    const glow = 0.18 + state.trayPulse * 0.2;
    ctx.fillStyle = `rgba(255,255,255,${glow})`;
    ctx.beginPath();
    ctx.ellipse(machine.trayShadow.x, machine.trayShadow.y, 44, 14, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    drawBall(state.displayBall, state.trayPulse * 1.8);
  }

  if (state.selectedBall && (state.drawPhase === "launch" || state.drawPhase === "settle")) {
    drawBall(state.selectedBall, 1.4);
  }
}

function drawStatus() {
  ctx.save();
  ctx.fillStyle = "rgba(23, 32, 58, 0.88)";
  ctx.font = "700 18px SUIT";
  ctx.textAlign = "left";
  ctx.fillText(
    state.autoDrawPending > 0
      ? "연속 추첨 중... 남은 번호를 자동으로 계속 뽑습니다"
      : state.mode === "drawing"
        ? "추첨 중..."
        : state.drawnNumbers.length >= 6
          ? "6개 추첨 완료. 저장 처리 후 리셋할 수 있습니다"
          : "번호 뽑기를 눌러 공을 하나씩 추첨하세요",
    48,
    56
  );

  ctx.font = "800 28px Black Han Sans";
  ctx.fillStyle = "#ffffff";
  ctx.fillText("LOTTO LIVE", 48, 96);

  ctx.font = "700 18px SUIT";
  ctx.fillStyle = "#17306d";
  ctx.fillText(`남은 공 ${state.availableNumbers.length}개`, 738, 84);
  ctx.fillText(`현재 추첨 ${totalDrawnCount()}/6`, 738, 112);

  if (state.sparkleTime > 0) {
    const latest = state.drawnNumbers.at(-1);
    const alpha = clamp(state.sparkleTime, 0, 1);
    ctx.fillStyle = `rgba(240, 67, 104, ${alpha * 0.9})`;
    ctx.font = "800 34px Black Han Sans";
    ctx.fillText(`DRAW! ${latest}`, 700, 162);
  }

  ctx.restore();
}

function render() {
  ctx.clearRect(0, 0, WIDTH, HEIGHT);
  drawBackground();
  drawMachineFrame();
  drawGlassGlobe();
  drawGlobeBalls();
  drawTrayBall();
  drawStatus();
}

function frame(timestamp) {
  if (!state.lastTimestamp) {
    state.lastTimestamp = timestamp;
  }

  const elapsed = Math.min((timestamp - state.lastTimestamp) / 1000, 1 / 24);
  state.lastTimestamp = timestamp;
  update(elapsed);
  render();
  requestAnimationFrame(frame);
}

function renderGameToText() {
  return JSON.stringify({
    coordinateSystem: {
      origin: "top-left",
      xDirection: "right",
      yDirection: "down",
      width: WIDTH,
      height: HEIGHT,
    },
    mode: state.mode,
    drawPhase: state.drawPhase,
    machine: {
      remainingBalls: state.availableNumbers.length,
      globeCenter: machine.globe,
      chuteEnd: machine.chuteEnd,
      trayRest: machine.trayRest,
    },
    drawnNumbers: state.drawnNumbers,
    activeBall: state.selectedBall
      ? {
          number: state.selectedBall.number,
          x: Math.round(state.selectedBall.x),
          y: Math.round(state.selectedBall.y),
        }
      : null,
    trayBall: state.displayBall
      ? {
          number: state.displayBall.number,
          x: Math.round(state.displayBall.x),
          y: Math.round(state.displayBall.y),
        }
      : null,
    autoDrawRemaining: state.autoDrawPending,
    ticket: {
      currentTicketPersisted: state.currentTicketPersisted,
      autoLinkConsumed: state.autoLinkConsumed,
      hasPrefetchedAdLink: Boolean(state.adLinkUrl),
      saveStatus: saveStatusEl?.textContent || "",
    },
    controls: {
      canDraw: !drawButton.disabled,
      canAutoDraw: !drawAllButton.disabled,
      canReset: true,
      keyboardShortcuts: ["Space: draw", "A: auto draw", "R: reset"],
    },
  });
}

function handleSingleDrawTrigger() {
  beginDraw();
}

function handleAutoDrawTrigger() {
  queueAutoDrawAll();
}

drawButton.addEventListener("click", handleSingleDrawTrigger);
drawAllButton.addEventListener("click", handleAutoDrawTrigger);
resetButton.addEventListener("click", resetGame);
window.addEventListener("keydown", (event) => {
  if (event.code === "Space") {
    event.preventDefault();
    handleSingleDrawTrigger();
  }

  if (event.key === "a" || event.key === "A") {
    handleAutoDrawTrigger();
  }

  if (event.key === "r" || event.key === "R") {
    resetGame();
  }
});

window.render_game_to_text = renderGameToText;
window.advanceTime = async (ms) => {
  const steps = Math.max(1, Math.round(ms / (1000 / 60)));
  for (let i = 0; i < steps; i += 1) {
    update(FIXED_DT);
  }
  render();
};

resetGame();
render();
void preloadAdLink();
requestAnimationFrame(frame);
