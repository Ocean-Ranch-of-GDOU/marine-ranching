const colors = ["#ff5b57", "#27ae60", "#2d7ff9", "#ef8c2f", "#7f56d9"];
let mapOffset = { x: -220, y: -60 };
let mapDragState = null;

async function loadDashboard() {
    const response = await fetch("/api/dashboard");
    const data = await response.json();
    renderDashboard(data);
}

function renderDashboard(data) {
    document.getElementById("farmName").textContent = data.farm_name;
    document.getElementById("updatedAt").textContent = data.updated_at || "--";

    renderMap(data.stations || []);
    renderTable(data.stations || []);
    renderAlarms(data.alarms || []);
    drawLineChart("temperatureChart", data.temperature_history || [], data.stations || [], "temperature", "°C");
    drawLineChart("feedingChart", data.feeding_history || [], data.stations || [], "feeding", "%");
    renderChartAxis("temperatureAxis", data.temperature_history || []);
    renderChartAxis("feedingAxis", data.feeding_history || []);
}

function renderMap(stations) {
    const panel = document.getElementById("mapPanel");
    panel.innerHTML = "";

    stations.forEach((station, index) => {
        const marker = document.createElement("div");
        marker.className = "map-marker";
        marker.style.left = `${station.position?.x ?? (20 + index * 20)}%`;
        marker.style.top = `${station.position?.y ?? (30 + index * 12)}%`;
        marker.style.setProperty("--marker-color", station.color || colors[index % colors.length]);

        marker.innerHTML = `
            <div class="label">${station.name}</div>
            <div class="pin"></div>
            <div class="meta">
                ${station.mode}
                <br>余料 ${formatValue(station.remaining_feed, "%")}
            </div>
        `;
        panel.appendChild(marker);
    });

    clampMapOffset();
    applyMapOffset();
}

function initializeMapDrag() {
    const viewport = document.getElementById("mapViewport");
    const resetButton = document.getElementById("mapResetButton");

    if (!viewport || viewport.dataset.dragReady === "true") {
        return;
    }

    viewport.dataset.dragReady = "true";

    const startDrag = (clientX, clientY) => {
        mapDragState = {
            startX: clientX,
            startY: clientY,
            originX: mapOffset.x,
            originY: mapOffset.y
        };
        viewport.classList.add("dragging");
    };

    const updateDrag = (clientX, clientY) => {
        if (!mapDragState) {
            return;
        }
        mapOffset = {
            x: mapDragState.originX + (clientX - mapDragState.startX),
            y: mapDragState.originY + (clientY - mapDragState.startY)
        };
        clampMapOffset();
        applyMapOffset();
    };

    const stopDrag = () => {
        mapDragState = null;
        viewport.classList.remove("dragging");
    };

    viewport.addEventListener("mousedown", (event) => {
        if (event.button !== 0) {
            return;
        }
        event.preventDefault();
        startDrag(event.clientX, event.clientY);
    });

    window.addEventListener("mousemove", (event) => updateDrag(event.clientX, event.clientY));
    window.addEventListener("mouseup", stopDrag);

    viewport.addEventListener("touchstart", (event) => {
        const touch = event.touches[0];
        if (!touch) {
            return;
        }
        startDrag(touch.clientX, touch.clientY);
    }, { passive: true });

    window.addEventListener("touchmove", (event) => {
        const touch = event.touches[0];
        if (!touch) {
            return;
        }
        updateDrag(touch.clientX, touch.clientY);
    }, { passive: true });
    window.addEventListener("touchend", stopDrag);

    if (resetButton) {
        resetButton.addEventListener("click", () => {
            mapOffset = { x: -220, y: -60 };
            clampMapOffset();
            applyMapOffset();
        });
    }
}

function clampMapOffset() {
    const viewport = document.getElementById("mapViewport");
    const panel = document.getElementById("mapPanel");

    if (!viewport || !panel) {
        return;
    }

    const minX = Math.min(0, viewport.clientWidth - panel.offsetWidth);
    const minY = Math.min(0, viewport.clientHeight - panel.offsetHeight);
    mapOffset.x = Math.max(minX, Math.min(0, mapOffset.x));
    mapOffset.y = Math.max(minY, Math.min(0, mapOffset.y));
}

function applyMapOffset() {
    const panel = document.getElementById("mapPanel");
    if (!panel) {
        return;
    }
    panel.style.transform = `translate(${mapOffset.x}px, ${mapOffset.y}px)`;
    panel.style.willChange = mapDragState ? "transform" : "auto";
}

function renderTable(stations) {
    const tbody = document.getElementById("stationTableBody");
    tbody.innerHTML = "";

    stations.forEach((station, index) => {
        const tr = document.createElement("tr");
        const color = station.color || colors[index % colors.length];
        tr.innerHTML = `
            <td><span class="badge" style="color:${color}">${station.name}</span></td>
            <td>${station.mode}</td>
            <td>${formatValue(station.temperature, "°C")}</td>
            <td>${formatValue(station.oxygen, "mg/L")}</td>
            <td>${formatValue(station.feeding_level, "%")}</td>
            <td>${formatValue(station.remaining_feed, "%")}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderAlarms(alarms) {
    const panel = document.getElementById("alarmList");
    panel.innerHTML = "";

    if (!alarms.length) {
        const empty = document.createElement("div");
        empty.className = "alarm-empty";
        empty.textContent = "当前未发现异常告警";
        panel.appendChild(empty);
        return;
    }

    alarms.forEach((alarm) => {
        const item = document.createElement("div");
        item.className = "alarm-card";
        item.innerHTML = `
            <div class="alarm-meta">
                <span>${alarm.time || "--"}</span>
                <span>${alarm.status || "active"}</span>
            </div>
            <div class="alarm-title">${alarm.type || "系统告警"} / ${alarm.originator || "未知设备"}</div>
            <div class="alarm-message">${alarm.message || "暂无详细描述"}</div>
        `;
        panel.appendChild(item);
    });
}

function drawLineChart(canvasId, history, stations, mode, unit) {
    const canvas = document.getElementById(canvasId);
    fitChartCanvas(canvas);
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth * dpr;
    const height = canvas.clientHeight * dpr;

    if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
    }

    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, width, height);

    const padding = { top: 18, right: 20, bottom: 46, left: 48 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;
    const points = history.length;
    const seriesCount = stations.length;

    const allValues = history.flatMap((item) => item.values || []);
    const minValue = mode === "feeding" ? 0 : Math.floor(Math.min(...allValues, 15) - 2);
    const maxValue = mode === "feeding" ? 100 : Math.ceil(Math.max(...allValues, 30) + 2);

    ctx.strokeStyle = "rgba(25, 50, 77, 0.12)";
    ctx.lineWidth = 1;
    ctx.font = `${12 * dpr}px sans-serif`;
    ctx.fillStyle = "#6e8297";

    for (let i = 0; i < 5; i++) {
        const y = padding.top + (plotHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();

        const value = maxValue - ((maxValue - minValue) / 4) * i;
        ctx.fillText(`${value.toFixed(0)}${unit}`, 8 * dpr, y + 4);
    }

    if (!points || !seriesCount) {
        return;
    }

    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top + plotHeight);
    ctx.lineTo(width - padding.right, padding.top + plotHeight);
    ctx.stroke();

    stations.forEach((station, stationIndex) => {
        const color = station.color || colors[stationIndex % colors.length];
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.5 * dpr;
        ctx.beginPath();

        history.forEach((item, pointIndex) => {
            const raw = item.values?.[stationIndex] ?? 0;
            const x = padding.left + (plotWidth * pointIndex) / Math.max(points - 1, 1);
            const y = padding.top + ((maxValue - raw) / (maxValue - minValue)) * plotHeight;
            if (pointIndex === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
    });

    renderLegend(
        canvasId === "temperatureChart" ? "temperatureLegend" : "feedingLegend",
        stations,
        mode === "temperature" ? "temperature" : "feeding_level"
    );
    fitChartCanvas(canvas);
}

function renderChartAxis(elementId, history) {
    const target = document.getElementById(elementId);
    if (!target) {
        return;
    }

    target.innerHTML = "";
    if (!history.length) {
        return;
    }

    const slots = 6;
    for (let index = 0; index < slots; index += 1) {
        const historyIndex = Math.min(
            history.length - 1,
            Math.round((index * (history.length - 1)) / Math.max(slots - 1, 1))
        );
        const item = document.createElement("span");
        item.textContent = history[historyIndex]?.time || "";
        target.appendChild(item);
    }
}

function fitChartCanvas(canvas) {
    if (!canvas) {
        return;
    }

    const panel = canvas.closest(".chart-panel");
    const head = panel?.querySelector(".panel-head");
    const axis = panel?.querySelector(".chart-axis-labels");
    const legend = panel?.querySelector(".chart-legend");

    if (!panel || !head || !axis || !legend) {
        return;
    }

    const availableHeight = panel.clientHeight - head.offsetHeight - axis.offsetHeight - legend.offsetHeight - 28;
    const targetHeight = Math.max(92, Math.min(132, availableHeight));
    canvas.style.height = `${targetHeight}px`;
    canvas.style.minHeight = `${targetHeight}px`;
    canvas.style.maxHeight = `${targetHeight}px`;
}

function renderLegend(elementId, stations, metric) {
    const target = document.getElementById(elementId);
    target.innerHTML = "";

    stations.forEach((station, index) => {
        const item = document.createElement("div");
        item.className = "legend-item";
        item.innerHTML = `
            <span class="legend-color" style="background:${station.color || colors[index % colors.length]}"></span>
            <span>${station.name} ${formatValue(station[metric], metric === "temperature" ? "°C" : "%")}</span>
        `;
        target.appendChild(item);
    });
}

function formatValue(value, unit) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return `-- ${unit}`;
    }
    return `${Number(value).toFixed(1)} ${unit}`;
}

function initializeMonitorModal() {
    const backdrop = document.getElementById("monitorModalBackdrop");
    const closeButton = document.getElementById("monitorModalClose");
    const triggerButton = document.getElementById("monitorPreviewTrigger");
    const toolbarButtons = Array.from(document.querySelectorAll(".monitor-toolbar-button"));
    const cameraSelect = document.getElementById("monitorCameraSelect");
    const cameraName = document.getElementById("monitorCameraName");
    const videoClock = document.getElementById("monitorVideoClock");
    const feedState = document.getElementById("monitorFeedState");
    const amountValue = document.getElementById("monitorAmountValue");
    const timeValue = document.getElementById("monitorTimeValue");
    const intervalValue = document.getElementById("monitorIntervalValue");
    const actionFeedback = document.getElementById("monitorActionFeedback");

    if (!backdrop || !closeButton || !triggerButton || backdrop.dataset.ready === "true") {
        return;
    }

    backdrop.dataset.ready = "true";

    const actionState = {
        amount: "12.5 kg",
        time: "10:30",
        interval: "15 min",
        running: false,
    };

    function updateClock() {
        if (!videoClock) {
            return;
        }
        videoClock.textContent = new Date().toLocaleTimeString("zh-CN", { hour12: false });
    }

    function syncMonitorStatus() {
        if (amountValue) {
            amountValue.textContent = actionState.amount;
        }
        if (timeValue) {
            timeValue.textContent = actionState.time;
        }
        if (intervalValue) {
            intervalValue.textContent = actionState.interval;
        }
        if (feedState) {
            feedState.textContent = actionState.running ? "投喂执行中" : "待机中";
        }
    }

    function setFeedback(message) {
        if (actionFeedback) {
            actionFeedback.textContent = message;
        }
    }

    triggerButton.addEventListener("click", () => {
        updateClock();
        syncMonitorStatus();
        backdrop.hidden = false;
    });

    closeButton.addEventListener("click", () => {
        backdrop.hidden = true;
    });

    backdrop.addEventListener("click", (event) => {
        if (event.target === backdrop) {
            backdrop.hidden = true;
        }
    });

    window.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            backdrop.hidden = true;
        }
    });

    if (cameraSelect) {
        cameraSelect.addEventListener("change", () => {
            if (cameraName) {
                cameraName.textContent = cameraSelect.value;
            }
            setFeedback(`已切换至${cameraSelect.value}`);
        });
    }

    toolbarButtons.forEach((button) => {
        button.addEventListener("click", () => {
            toolbarButtons.forEach((item) => item.classList.remove("is-active"));
            button.classList.add("is-active");

            const action = button.dataset.action;
            if (action === "amount") {
                actionState.amount = actionState.amount === "12.5 kg" ? "15.0 kg" : "12.5 kg";
                syncMonitorStatus();
                setFeedback(`投喂量已调整为 ${actionState.amount}`);
            } else if (action === "time") {
                actionState.time = actionState.time === "10:30" ? "11:00" : "10:30";
                syncMonitorStatus();
                setFeedback(`投喂时间已设置为 ${actionState.time}`);
            } else if (action === "interval") {
                actionState.interval = actionState.interval === "15 min" ? "20 min" : "15 min";
                syncMonitorStatus();
                setFeedback(`投喂间隔已切换为 ${actionState.interval}`);
            } else if (action === "start") {
                actionState.running = !actionState.running;
                button.textContent = actionState.running ? "停止投喂" : "开始投喂";
                syncMonitorStatus();
                setFeedback(actionState.running ? "投喂任务已启动，设备正在执行。" : "投喂任务已停止，设备恢复待机。");
            }
        });
    });

    updateClock();
    syncMonitorStatus();
    setInterval(updateClock, 1000);
}

loadDashboard();
initializeMapDrag();
initializeMonitorModal();
setInterval(loadDashboard, 5000);
window.addEventListener("resize", () => {
    clampMapOffset();
    loadDashboard();
});
