<template>
  <div id="canvas-timeline-container" class="timeline-container">
    <div class="toolbar">
      <div class="toolbar-item">
        <span>
          <input type="checkbox" id="showTasksStatus" v-model="showTasksStatus">
          <label for="showTasksStatus">Show Tasks Status</label>
        </span>
        <span v-if="this.selectedAssets.length" >
          <input type="checkbox" id="showSelectedAssets" v-model="showSelectedAssets">
          <label for="showSelectedAssets">Show Selected Assets</label>
        </span>
        <button @click="fitTimelineView">Fit View</button>
      </div>
    </div>

    <canvas id="canvas-timeline"></canvas>
    <canvas id="canvas-timeline-text"
      @mousedown="onMouseEvent($event)"
      @mouseup="onMouseEvent($event)"
      @mousemove="onMouseEvent($event)"
      @mouseleave="onMouseEvent($event)"
      @wheel="onScroll($event)"
    >
    </canvas>
  </div>
</template>

<script>

import { UIRenderer } from 'uirenderer-canvas';

export default {
  name: "TimelineView",
  props: {
    taskTypes: Array,
    taskStatuses: Array,
    sequences: Array,
    shots: Array,
    totalFrames: Number,
    fps: Number,
    currentFrame: Number,
    selectedAssets: Array,
  },
  data () {
    return {
      // View user configuration.
      showTasksStatus: true,
      showSelectedAssets: true,
      // Canvas & rendering context.
      canvas: null,
      canvasText: null,
      uiRenderer: null,
      ui2D: null,
      // Runtime state
      timelineRange: { x: 0 , w: 100 }, // Position where the timeline starts and the width, in canvas coordinates.
      timelineView: { x: 0, w: 100 }, // Window of the visible timeline, mapped to occupy timelineRange. Represents pan and zoom.
      channelNamesWidth: 50, // Width in px of the longest channel name. Channel name area is this value + timeline.padX.
      // Interaction.
      isMouseDragging: { LMB: false, MMB: false, },
      gesture: {
        initialMouseCoords: null,
        initialViewRect: null,
      },
      // "Current" elements for the playhead position.
      shotForCurrentFrame: null,
    }
  },
  computed: {
    uiConfig: function() {
      // Layout constants.
      return {
        fontSize: 12,
        margin: {x: 15, top: 22, bottom: 7}, // Spacing around the contents of the timeline canvas. One side, in px.
        currFrameHighlight: { width: 1.5, color: [0.85, 0.8, 0.7, 1.0], },
        castingHighlight: { width: 1.5, color: [0.2, 0.58, 0.8, 1.0], },
        playhead: {
          padY: 8, // From the absolute top. Ignores 'margin'.
          triangle: {width: 12.0, height: 8.0, flatHeight: 4.0},
          lineWidth: 2.0,
          color: [0.85, 0.8, 0.7, 1.0],
          shadow: { radius: 1.5, color: [0, 0, 0, 0.5] },
        },
        timeline: {
          padX: 20,
          frame0Color: [0.36, 0.36, 0.36, 1.0],
        },
        sequences: {
          fontPad: {x: 2, top: 3, bottom: 1},
          fontSize: 10,
          height: 6,
          channelHeight: 3 + 10 + 1 + 6 + 4, // 24, matches channels.
          corner: 0,
        },
        shots: {
          height: 27,
          channelHeight: 40,
          lineWidth: 1,
          corner: 0,
          color: [0.3, 0.3, 0.3, 1.0],
        },
        channels: {
          namePadX: 8,
          height: 24,
          contentHeight: 12,
          colorOdd: [0.167, 0.167, 0.167, 1.0],
          colorEven: [0.21, 0.21, 0.21, 1.0],
        }
      };
    },
    taskTypesForShots: function() {
      return this.taskTypes.filter(taskType => taskType.for_shots === true);
    }
  },
  watch: {
    showTasksStatus: function () {
      this.onChannelsUpdated();
    },
    showSelectedAssets: function () {
      this.onChannelsUpdated();
    },
    taskTypes: function () {
      this.onChannelsUpdated();
    },
    taskStatuses: function () {
      this.draw();
    },
    sequences: function () {
      this.draw();
    },
    shots: function () {
      this.draw();
    },
    currentFrame: function () {
      // Find the shot that should be highlighted.
      this.findShotForCurrentFrame();

      this.draw();
    },
    selectedAssets: function () {
      this.onChannelsUpdated();
    },
    totalFrames: function () {
      this.onVisibleFrameRangeUpdated();
    },
    timelineView: function () {
      this.onVisibleFrameRangeUpdated();
    },
  },
  mounted: function () {
    this.initCanvas();
    this.fitTimelineView();

    // Note: Image loading, if any, should go here.

    // Initial draw of this component.
    this.draw();
  },
  methods: {
    getCanvasRect: function () {
      return this.canvas.getBoundingClientRect();
    },

    clientToCanvasCoords: function (event) {
      let rect = this.getCanvasRect();
      return {
         x: event.clientX - rect.left,
         y: event.clientY - rect.top
      };
    },

    pxToFrame: function (canvasX) {
      // Convert from a pixel position in the canvas to a frame.
      const offset = this.timelineView.x - this.timelineRange.x; // Pan.
      const scale = this.timelineRange.w / this.timelineView.w; // Zoom.
      const timelineFracPx = offset + (canvasX - this.timelineRange.x) / scale;
      let newCurrentFrame = (timelineFracPx / this.timelineRange.w) * this.totalFrames;
      // Clamp to the edit's frame range.
      newCurrentFrame = Math.min(Math.max(newCurrentFrame, 0), this.totalFrames);
      // Return the closest frame.
      return Math.round(newCurrentFrame);
    },

    resizeCanvas: function (shouldDraw = true) {
      // Resize canvas height according to the number of channels and to the full available width.
      const canvasContainer = document.getElementById('canvas-timeline-container');
      let numChannels = 0;
      if (this.showSelectedAssets) { numChannels += this.selectedAssets.length; }
      if (this.showTasksStatus) { numChannels += this.taskTypesForShots.length; }
      this.canvas.width = canvasContainer.offsetWidth;
      this.canvas.height = this.uiConfig.margin.top
          + this.uiConfig.sequences.channelHeight
          + this.uiConfig.shots.channelHeight
          + this.uiConfig.channels.height * numChannels
          + this.uiConfig.margin.bottom;

      this.canvasText.width = this.canvas.width;
      this.canvasText.height = this.canvas.height;

      // Store the view window before the resize. Pan and zoom will be preserved.
      const offset = this.timelineView.x - this.timelineRange.x; // Pan.
      const scale = this.timelineRange.w / this.timelineView.w; // Zoom.

      // Update cached timeline horizontal range.
      const margin = this.uiConfig.margin;
      const timelineX = margin.x + this.channelNamesWidth + this.uiConfig.timeline.padX;
      this.timelineRange.x = timelineX;
      this.timelineRange.w = this.canvas.width - timelineX - margin.x;

      // Update the view window to show the same frame range as before the resize.
      this.timelineView.x = this.timelineRange.x + offset;
      this.timelineView.w = this.timelineRange.w / scale;

      if (shouldDraw) {
        this.draw();
      }
    },

    initCanvas: function () {
      // Create the rendering setup.
      this.canvas = document.getElementById('canvas-timeline');
      this.uiRenderer = new UIRenderer(this.canvas, this.draw);

      this.canvasText = document.getElementById('canvas-timeline-text');
      this.ui2D = this.canvasText.getContext("2d");

      // Resize the canvas to fill browser window dynamically
      window.addEventListener('resize', this.resizeCanvas, false);

      // Call the re-size once to trigger the sizing, but avoid drawing because
      // images (if any) haven't been created yet.
      this.resizeCanvas(false);
    },

    updateChannelNamesWidth: function () {
      let channelNamesWidth = this.ui2D.measureText("Sequences").width;
      for (const task of this.taskTypesForShots) {
        channelNamesWidth = Math.max(channelNamesWidth, this.ui2D.measureText(task.name).width);
      }
      for (const asset of this.selectedAssets) {
        channelNamesWidth = Math.max(channelNamesWidth, this.ui2D.measureText(asset.name).width);
      }

      this.channelNamesWidth = channelNamesWidth;
    },

    draw: function () {
      const rect = this.getCanvasRect();
      const ui = this.uiRenderer;
      ui.beginFrame();

      // Setup style for the text rendering in the overlaid canvas for text.
      const fontSize = this.uiConfig.fontSize;
      this.ui2D.clearRect(0, 0, this.canvasText.width, this.canvasText.height);
      this.ui2D.fillStyle = "rgb(220, 220, 220)";
      this.ui2D.font = fontSize + "px sans-serif";
      this.ui2D.textAlign = "left";
      this.ui2D.textBaseline = "top";
      this.ui2D.shadowOffsetX = 1;
      this.ui2D.shadowOffsetY = 1;
      this.ui2D.shadowBlur = 2;
      this.ui2D.shadowColor = 'rgba(0, 0, 0, 0.5)';

      // Calculate size and position of elements.
      const margin = this.uiConfig.margin;
      const numChannels = this.taskTypesForShots.length;
      const channelStep = this.uiConfig.channels.height;
      const timelinePadX = this.uiConfig.timeline.padX;
      const timelineX = this.timelineRange.x;
      const timelineW = this.timelineRange.w;
      const timelineTop = margin.top;
      const timelineBottom = rect.height - this.uiConfig.margin.bottom;
      const seqChannelHeight = this.uiConfig.sequences.channelHeight;
      const seqHeight = this.uiConfig.sequences.height;
      const seqTextPad = this.uiConfig.sequences.fontPad;
      const seqFontSize = this.uiConfig.sequences.fontSize;
      const seqPaddedTextHeight = seqTextPad.top + seqTextPad.bottom + seqFontSize;
      const seqTop = margin.top + seqPaddedTextHeight;
      const shotHeight = this.uiConfig.shots.height;
      const shotChannelHeight = this.uiConfig.shots.channelHeight;
      const shotChannelTop = margin.top + seqChannelHeight;
      const shotTop = shotChannelTop + Math.round((shotChannelHeight - shotHeight) / 2);
      const channelStartY = margin.top + seqChannelHeight + shotChannelHeight;
      const channelContentPadY = Math.round((channelStep - this.uiConfig.channels.contentHeight) / 2);
      const channelBGWidth = this.channelNamesWidth + timelinePadX + timelineW;
      const channelColor0 = this.uiConfig.channels.colorEven;
      const channelColor1 = this.uiConfig.channels.colorOdd;

      // Draw channel strips background.
      ui.addRect(margin.x, margin.top, channelBGWidth, seqChannelHeight, channelColor0);
      ui.addRect(margin.x, shotChannelTop, channelBGWidth, shotChannelHeight, channelColor1);
      let channelY = channelStartY;
      for (let i=0; i < numChannels; i++) {
        const color = i % 2 === 1 ? channelColor1 : channelColor0;
        ui.addRect(margin.x, channelY, channelBGWidth, channelStep, color);
        channelY += channelStep;
      }

      // Set the timeline area view window.
      const offset = this.timelineView.x - this.timelineRange.x; // Pan.
      const scale = this.timelineRange.w / this.timelineView.w; // Zoom.
      const view = ui.pushView(
        this.timelineRange.x, 0, this.timelineRange.w, rect.height,
        [scale, 1], [offset, 0]
      );

      // Draw shots.
      const shotsStyle = this.uiConfig.shots;
      const taskHeight = this.uiConfig.channels.contentHeight;
      for (const shot of this.shots) {
        const startPos = timelineX + shot.startFrame * timelineW / this.totalFrames;
        const endFrame = shot.startFrame + shot.durationSeconds * this.fps;
        const endPos = timelineX + endFrame * timelineW / this.totalFrames;
        const shotWidth = endPos - startPos;
        ui.addFrame(startPos, shotTop, shotWidth, shotHeight, shotsStyle.lineWidth, shotsStyle.color, shotsStyle.corner);
      }
      // Draw a border around the shot corresponding to the current frame.
      if (this.shotForCurrentFrame) {
        const shot = this.shotForCurrentFrame;
        const rim = this.uiConfig.currFrameHighlight;
        const startPos = timelineX + shot.startFrame * timelineW / this.totalFrames;
        const endFrame = shot.startFrame + shot.durationSeconds * this.fps;
        const endPos = timelineX + endFrame * timelineW / this.totalFrames;
        const shotWidth = endPos - startPos;
        ui.addFrame(startPos, shotTop, shotWidth, shotHeight, rim.width, rim.color, shotsStyle.corner);
      }

      // Draw selected assets.
      channelY = channelStartY + channelContentPadY;
      if (this.showSelectedAssets) {
        for (const asset of this.selectedAssets) {
          // Get the contiguous frame ranges where this asset appears.
          let {startPos, widths} = this.getRangesWhere((shot) => { return asset.shots.includes(shot.id); });
          // Draw a rect for each range of shots.
          for (let i = 0; i < startPos.length; i++) {
            ui.addRect(startPos[i], channelY, widths[i], taskHeight, this.uiConfig.castingHighlight.color);
          }
          channelY += channelStep;
        }
      }

      // Draw task statuses.
      if (this.showTasksStatus) {
        for (const taskType of this.taskTypesForShots) { // e.g. "Animation"
          for (const status of this.taskStatuses) { // e.g. "Done"
            // Get the contiguous frame ranges for this task status.
            let {startPos, widths} = this.getRangesWhere((shot) => {
              // Search if the shot has a status for the current task type.
              for (const taskStatus of shot.tasks) {
                if (taskStatus.task_type_id === taskType.id) {
                  // It does, check if the status for this task matches the requested one.
                  return (taskStatus.task_status_id === status.id);
                }
              }
              return false;
            });
            // Draw a rect for each range of shots.
            for (let i = 0; i < startPos.length; i++) {
              ui.addRect(startPos[i], channelY, widths[i], taskHeight, status.color);
            }
          }
          channelY += channelStep;
        }
      }

      // Draw sequences
      const seqCorner = this.uiConfig.sequences.corner;
      this.ui2D.font = seqFontSize + "px sans-serif";
      for (const sequence of this.sequences) {
        // Find continuous ranges of shots that belong to this sequence.
        // In theory, a sequence has a single contiguous range, but in practice,
        // there might shots mistakenly assigned to sequences or shots missing.
        let {startPos, widths} = this.getRangesWhere((shot) => sequence.id === shot.sequence_id);
        // Draw a rect for each range of shots belonging to this sequence.
        for (let i = 0; i < startPos.length; i++) {
          ui.addRect(startPos[i], seqTop, widths[i], seqHeight, sequence.color, seqCorner);
        }
        if (startPos.length) {
          // Draw the sequence name in the visible space above the first range.
          const clipL = Math.max(view.transformPosX(startPos[0]), view.left);
          const clipR = Math.min(view.transformPosX(startPos[0] + widths[0]), view.right);
          const clippedWidth = clipR - clipL;
          const availableWidth = clippedWidth - seqTextPad.x * 2 - this.ui2D.measureText("..").width;
          if (availableWidth > 0) {
            let name = sequence.name;
            while (this.ui2D.measureText(name).width > availableWidth) {
              name = name.slice(0, -1);
            }
            if (name !== sequence.name) {
              name += "..";
            }
            this.ui2D.fillText(name, clipL + seqTextPad.x, seqTop - (seqFontSize + seqTextPad.bottom));
          }
        }
      }
      this.ui2D.font = fontSize + "px sans-serif";

      ui.popView();

      // Render timeline start as a line between the channel names and the timeline content.
      // The timeline content might not start at frame 0, so the line is important.
      const frame0LineColor = this.uiConfig.timeline.frame0Color;
      ui.addLine([timelineX, timelineTop], [timelineX, timelineBottom], 1, frame0LineColor);

      // Playhead
      // Update the playhead position according to the current frame.
      // The playhead position moves with the current zoom and pan, but the playhead geometry is unscaled.
      const playheadPos = view.transformPosX(timelineX + this.currentFrame / this.totalFrames * timelineW);
      if (playheadPos >= view.left && playheadPos <= view.right) {
        const playhead = this.uiConfig.playhead;
        const triangle = this.uiConfig.playhead.triangle;
        const triangleTop = playhead.padY + playhead.triangle.flatHeight;
        const triangleHalfWidth = (triangle.width - 0.5) * 0.5;
        // Shadow.
        const shadowRadius = playhead.shadow.radius;
        const shadowColor = playhead.shadow.color;
        ui.addLine(
          [playheadPos + shadowRadius, playhead.padY + triangle.height + shadowRadius], // Triangle tip. (Up)
          [playheadPos + shadowRadius, rect.height - playhead.padY + shadowRadius], // (Down)
          playhead.lineWidth, shadowColor
        );
        ui.addLine(
          [playheadPos,                     triangleTop + triangle.height], // Center, down.
          [playheadPos + triangleHalfWidth, triangleTop], // Top, right.
          3, shadowColor
        );
        ui.addLine(
          [playheadPos + triangleHalfWidth + shadowRadius * 0.8, triangleTop], // Top, right.
          [playheadPos + triangleHalfWidth + shadowRadius * 0.8, playhead.padY + shadowRadius], // Toppest, right.
          2, shadowColor
        );
        // Playhead.
        ui.addLine(
          [playheadPos, playhead.padY + triangle.height], // Triangle tip. (Up)
          [playheadPos, rect.height - playhead.padY], // (Down)
          playhead.lineWidth, playhead.color
        );
        ui.addTriangle(
          [playheadPos,                     triangleTop + triangle.height], // Center, down.
          [playheadPos - triangleHalfWidth, triangleTop], // Top, left.
          [playheadPos + triangleHalfWidth, triangleTop], // Top, right.
          playhead.color
        );
        ui.addRect(
          playheadPos - triangle.width * 0.5, playhead.padY,
          triangle.width + 1, playhead.triangle.flatHeight + 1, playhead.color, 1
        );
      }

      const halfFontSize = fontSize / 2;
      const textX = margin.x + this.uiConfig.channels.namePadX;
      let textY = margin.top + Math.round(seqChannelHeight / 2) - halfFontSize;
      this.ui2D.fillText("Sequences", textX, textY);
      textY = shotChannelTop + Math.round(shotChannelHeight / 2) - halfFontSize;
      this.ui2D.fillText("Shots", textX, textY);
      textY = channelStartY + Math.round(channelStep / 2) - halfFontSize;
      if (this.showSelectedAssets) {
        for (const asset of this.selectedAssets) {
          this.ui2D.fillText(asset.name, textX, textY);
          textY += channelStep;
        }
      }
      if (this.showTasksStatus) {
        for (const task of this.taskTypesForShots) {
          this.ui2D.fillText(task.name, textX, textY);
          textY += channelStep;
        }
      }

      // Draw the frame.
      ui.draw();
    },

    // Find continuous ranges of shots where the given condition is true.
    getRangesWhere: function (hasProp) {
      let currRange = -1;
      let startFrames = [];
      let endFrames = [];

      for (const shot of this.shots) {
        if (hasProp(shot)) {
          if (currRange === -1) {
            startFrames.push(shot.startFrame);
            currRange = shot.startFrame + shot.durationSeconds * this.fps;
          } else if (currRange === shot.startFrame) {
            currRange += shot.durationSeconds * this.fps;
          } else {
            endFrames.push(currRange);
            startFrames.push(shot.startFrame);
            currRange = shot.startFrame + shot.durationSeconds * this.fps;
          }
        } else if (currRange !== -1) {
          endFrames.push(currRange);
          currRange = -1;
        }
      }
      endFrames.push(currRange);

      // Convert frame ranges to X positions on the timeline area
      const timelineX = this.timelineRange.x;
      const timelineFrameW = this.timelineRange.w / this.totalFrames;
      let startPos = [];
      let widths = [];
      for (let i = 0; i < startFrames.length; i++) {
        startPos.push(timelineX + startFrames[i] * timelineFrameW);
        widths.push((endFrames[i] - startFrames[i]) * timelineFrameW);
      }
      return {startPos, widths};
    },

    findShotForCurrentFrame: function () {
      let shotForCurrentFrame = null;
      for (const shot of this.shots) {
        if(shot.startFrame > this.currentFrame)
          break;
        shotForCurrentFrame = shot;
      }
      this.shotForCurrentFrame = shotForCurrentFrame;
    },

    setCurrentFrame: function (canvasX) {
      this.$emit('set-current-frame', this.pxToFrame(canvasX));
    },

    onVisibleFrameRangeUpdated: function() {
      const startFrame = this.pxToFrame(this.timelineRange.x);
      const endFrame = this.pxToFrame(this.timelineRange.x + this.timelineRange.w);
      this.$emit('set-timeline-visible-frames', [startFrame, endFrame]);

      this.draw();
    },

    onChannelsUpdated: function() {
      // Update the width needed to show the channel names.
      this.updateChannelNamesWidth();
      // Resize the timeline area to fit all channels (that are visible).
      this.resizeCanvas();

      // Ensure the timeline area view doesn't go under the channel names.
      const overlap = this.timelineRange.x - this.timelineView.x;
      if (overlap > 0) {
        this.timelineView.x = this.timelineRange.x;
        this.timelineView.w -= overlap;
      }
      // draw() will be trigger by the update to timelineView.
    },

    fitTimelineView: function() {
      this.timelineView = { x: this.timelineRange.x, w: this.timelineRange.w };
    },

    panTimelineView: function(deltaX, initialX) {
      const viewWidth = this.timelineView.w;
      const scaleFactor = this.timelineView.w / this.timelineRange.w;
      let newViewRectX = initialX - deltaX * scaleFactor;
      newViewRectX = Math.max(newViewRectX, this.timelineRange.x);
      newViewRectX = Math.min(newViewRectX, this.timelineRange.x + this.timelineRange.w - viewWidth);

      this.timelineView = { x: newViewRectX, w: viewWidth };
    },

    zoomTimelineView: function(pivotX, delta) {
      let pivotFrac = (pivotX - this.timelineRange.x) / this.timelineRange.w;
      pivotFrac = Math.min(Math.max(0, pivotFrac), 1);

      let widthIncrease = delta * 2;
      if (this.timelineView.w + widthIncrease < 10) {
        widthIncrease = 0;
      }
      let viewPosX = this.timelineView.x - widthIncrease * pivotFrac;
      let viewWidth = this.timelineView.w + widthIncrease;
      viewPosX = Math.max(viewPosX, this.timelineRange.x);
      const viewRight = Math.min(viewPosX + viewWidth, this.timelineRange.x + this.timelineRange.w);
      viewWidth = viewRight - viewPosX;

      this.timelineView = { x: viewPosX, w: viewWidth };
    },

    onMouseEvent: function (event) {
      // Set a new playhead position when LMB clicking or dragging.
      if (this.isMouseDragging.LMB
        && (event.type === 'mousemove' || event.type === 'mouseup')) {
        const mouse = this.clientToCanvasCoords(event);
        this.setCurrentFrame(mouse.x);
      }

      // Pan when MMB dragging.
      if (event.type === 'mousedown' && event.button === 1) {
        this.gesture.initialMouseCoords = this.clientToCanvasCoords(event);
        this.gesture.initialViewRect = this.timelineView;
      }

      if (this.isMouseDragging.MMB
          && (event.type === 'mousemove' || event.type === 'mouseup')) {
        const mouse = this.clientToCanvasCoords(event);
        this.panTimelineView(mouse.x - this.gesture.initialMouseCoords.x, this.gesture.initialViewRect.x);
        //console.log(mouse, event.movementX, event.movementY, this.mmbxy.x - mouse.x);
      }

      // Update mouse capturing state.
      if (event.type === 'mousedown') {
        if      (event.button === 0) { this.isMouseDragging.LMB = true; }
        else if (event.button === 1) { this.isMouseDragging.MMB = true; }
      } else if (event.type === 'mouseup' ) {
        if      (event.button === 0) { this.isMouseDragging.LMB = false; }
        else if (event.button === 1) { this.isMouseDragging.MMB = false; }
      } else if (event.type === 'mouseleave') {
        this.isMouseDragging.LMB = false;
        this.isMouseDragging.MMB = false;
      }
    },

    onScroll: function (event) {
      const mouse = this.clientToCanvasCoords(event);
      if (event.deltaY !== 0) {
        this.zoomTimelineView(mouse.x, event.deltaY);
      }
      if (event.deltaX !== 0) {
         this.panTimelineView(-event.deltaX, this.timelineView.x);
      }
      // Prevent the full page from scrolling vertically.
      event.preventDefault();
    },

    onKeyDown: function (event) {
      if (event.key === "Home") {
        this.fitTimelineView();
      } else if (event.key === "ArrowRight") {
        const idx = this.shots.indexOf(this.shotForCurrentFrame);
        const newIdx = Math.min(this.shots.length, (idx === -1) ? 0 : idx + 1);
        this.$emit('set-current-frame', this.shots[newIdx].startFrame);
      } else if (event.key === "ArrowLeft") {
        const idx = this.shots.indexOf(this.shotForCurrentFrame);
        const newIdx = Math.max(0, (idx === -1) ? 0 : idx - 1);
        this.$emit('set-current-frame', this.shots[newIdx].startFrame);
      }
    }
  },

  created () {
    document.body.addEventListener('keydown', this.onKeyDown);
  },
  unmounted () {
    document.body.removeEventListener('keydown', this.onKeyDown);
  }
}

</script>

<style scoped>
canvas {
  display: block;
}

.timeline-container {
  position: relative;
  background-color: var(--panel-bg-color);
}
#canvas-timeline {
  position: absolute;
}
#canvas-timeline-text {
  position: absolute;
  z-index: 10;
}

label {
  padding-left: var(--spacer-1);
}
input {
  margin-left: 1rem;
  /* margin-right: -0.8rem; */
}
button {
  margin-left: 1.5rem;
}
</style>
