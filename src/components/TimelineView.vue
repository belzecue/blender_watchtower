<template>
  <div id="canvas-timeline-container">
    <canvas id="canvas-timeline"></canvas>
    <canvas id="canvas-timeline-text"
      @mousedown="onMouseEvent($event)"
      @mouseup="onMouseEvent($event)"
      @mousemove="onMouseEvent($event)"
      @mouseleave="onMouseEvent($event)"
    >
    </canvas>
  </div>
</template>

<script>

import { UIRenderer } from '../shading';

export default {
  name: "TimelineView",
  props: {
    taskTypes: Array,
    taskStatuses: Array,
    sequences: Array,
    shots: Array,
    currentFrame: Number,
    totalFrames: Number,
    fps: Number,
  },
  data () {
    return {
      canvas: null,
      canvasText: null,
      isPlayheadDraggable: false,
      uiRenderer: null,
      ui2D: null,
      uiElements: {
        margin: {x: 15, top: 22, bottom: 7}, // Spacing around the contents of the timeline canvas. One side, in px.
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
          height: 6,
          channelHeight: 16,
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
      },
      timelineRange: { x: 0 , w: 100},
    }
  },
  watch: {
    taskTypes: function () {
      this.resizeCanvas();
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
      this.draw();
    },
  },
  mounted: function () {
    this.initCanvas();

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

    resizeCanvas: function (shouldDraw = true) {
      const canvasContainer = document.getElementById('canvas-timeline-container');
      this.canvas.width = canvasContainer.offsetWidth;
      this.canvas.height = this.uiElements.margin.top
          + this.uiElements.sequences.channelHeight
          + this.uiElements.shots.channelHeight
          + this.uiElements.channels.height * this.taskTypes.length
          + this.uiElements.margin.bottom;

      this.canvasText.width = this.canvas.width;
      this.canvasText.height = this.canvas.height;

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

    draw: function () {

      const ui = this.uiRenderer;
      const rect = this.getCanvasRect();
      // Setup style for the text rendering in the overlaid canvas for text.
      this.ui2D.clearRect(0, 0, this.canvasText.width, this.canvasText.height);
      this.ui2D.fillStyle = "rgb(220, 220, 220)";
      this.ui2D.font = "12px sans-serif";
      this.ui2D.textAlign = "left";
      this.ui2D.textBaseline = "top";
      this.ui2D.shadowOffsetX = 1;
      this.ui2D.shadowOffsetY = 1;
      this.ui2D.shadowBlur = 2;
      this.ui2D.shadowColor = 'rgba(0, 0, 0, 0.5)';

      // Calculate size and position of elements.
      const margin = this.uiElements.margin;
      let channelNamesWidth = this.ui2D.measureText("Sequences").width;
      for (const task of this.taskTypes) {
        channelNamesWidth = Math.max(channelNamesWidth, this.ui2D.measureText(task.name).width);
      }
      const numChannels = this.taskTypes.length;
      const channelStep = this.uiElements.channels.height;
      const timelinePadX = this.uiElements.timeline.padX;
      const timelineX = margin.x + channelNamesWidth + timelinePadX;
      const timelineW = rect.width - timelineX - margin.x;
      const timelineTop = margin.top;
      const timelineBottom = rect.height - this.uiElements.margin.bottom;
      const seqHeight = this.uiElements.sequences.height;
      const seqChannelHeight = this.uiElements.sequences.channelHeight;
      const seqTop = margin.top + Math.round((seqChannelHeight - seqHeight) / 2);
      const shotHeight = this.uiElements.shots.height;
      const shotChannelHeight = this.uiElements.shots.channelHeight;
      const shotChannelTop = margin.top + seqChannelHeight;
      const shotTop = shotChannelTop + Math.round((shotChannelHeight - shotHeight) / 2);
      const channelStartY = margin.top + seqChannelHeight + shotChannelHeight;
      const channelContentPadY = Math.round((channelStep - this.uiElements.channels.contentHeight) / 2);
      const channelBGWidth = channelNamesWidth + timelinePadX + timelineW;
      const channelColor0 = this.uiElements.channels.colorEven;
      const channelColor1 = this.uiElements.channels.colorOdd;

      // Update cached timeline horizontal range.
      this.timelineRange.x = timelineX;
      this.timelineRange.w = timelineW;

      // Draw channel strips background.
      ui.addRect(margin.x, margin.top, channelBGWidth, seqChannelHeight, channelColor0);
      ui.addRect(margin.x, shotChannelTop, channelBGWidth, shotChannelHeight, channelColor1);
      let channelY = channelStartY;
      for (let i=0; i < numChannels; i++) {
        const color = i % 2 === 1 ? channelColor1 : channelColor0;
        ui.addRect(margin.x, channelY, channelBGWidth, channelStep, color);
        channelY += channelStep;
      }
      // Render timeline start as a line between the channel names and the timeline content.
      // The timeline content might not start at frame 0, so the line is important.
      const frame0LineColor = this.uiElements.timeline.frame0Color;
      ui.addLine([timelineX, timelineTop], [timelineX, timelineBottom], 1, frame0LineColor);

      // Draw shots and their tasks' status
      const shotsStyle = this.uiElements.shots;
      const taskHeight = this.uiElements.channels.contentHeight;
      for (const shot of this.shots) {
        const startPos = timelineX + shot.startFrame * timelineW / this.totalFrames;
        const endFrame = shot.startFrame + 1 + shot.durationSeconds * this.fps;
        const endPos = timelineX + endFrame * timelineW / this.totalFrames;
        const shotWidth = endPos - startPos;
        ui.addFrame(startPos, shotTop, shotWidth, shotHeight, shotsStyle.lineWidth, shotsStyle.color, shotsStyle.corner);

        // Draw task statuses
        channelY = channelStartY + channelContentPadY;
        for (const task of this.taskTypes) {
          for (const taskStatus of shot.tasks) {
            if (taskStatus.task_type_id === task.id) {
              for (const status of this.taskStatuses) {
                if (taskStatus.task_status_id === status.id) {
                  ui.addRect(startPos, channelY, shotWidth, taskHeight, status.color);
                  break;
                }
              }
              break;
            }
          }
          channelY += channelStep;
        }
      }

      // Draw sequences
      const seqCorner = this.uiElements.sequences.corner;
      for (const sequence of this.sequences) {
        // Find continuous ranges of shots that belong to this sequence.
        // In theory, a sequence has a single contiguous range, but in practice,
        // there might shots mistakenly assigned to sequences or shots missing.
        let currRange = -1;
        let startFrames = [];
        let endFrames = [];
        for (const shot of this.shots) {
          if (sequence.id === shot.sequence_id) {
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
        // Draw a rect for each range of shots belonging to this sequence.
        for (let i = 0; i < startFrames.length; i++) {
          const startPos = timelineX + startFrames[i] * timelineW / this.totalFrames;
          const endPos = timelineX + endFrames[i] * timelineW / this.totalFrames;
          ui.addRect(startPos, seqTop, endPos - startPos, seqHeight, sequence.color, seqCorner);
        }
      }

      // Playhead
      // Update the playhead position according to the current frame.
      const playheadPos = timelineX + this.currentFrame * timelineW / this.totalFrames;
      const playhead = this.uiElements.playhead;
      const triangle = this.uiElements.playhead.triangle;
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
          [playheadPos                    , triangleTop + triangle.height], // Center, down.
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
        [playheadPos                    , triangleTop + triangle.height], // Center, down.
        [playheadPos - triangleHalfWidth, triangleTop], // Top, left.
        [playheadPos + triangleHalfWidth, triangleTop], // Top, right.
        playhead.color
      );
      ui.addRect(
        playheadPos - triangle.width * 0.5, playhead.padY,
        triangle.width + 1, playhead.triangle.flatHeight + 1, playhead.color, 1
      );

      const textX = margin.x + this.uiElements.channels.namePadX;
      let textY = margin.top + Math.round(seqChannelHeight / 2) - 6; // 6 = font size / 2
      this.ui2D.fillText("Sequences", textX, textY);
      textY = shotChannelTop + Math.round(shotChannelHeight / 2) - 6;
      this.ui2D.fillText("Shots", textX, textY);
      textY = channelStartY + Math.round(channelStep / 2) - 6;
      for (const task of this.taskTypes) {
        this.ui2D.fillText(task.name, textX, textY);
        textY += channelStep;
      }

      // Draw the frame.
      ui.draw();
    },

    setCurrentFrame: function (canvasX) {
      let newCurrentFrame = (canvasX - this.timelineRange.x) / this.timelineRange.w * this.totalFrames;
      newCurrentFrame = Math.min(Math.max(newCurrentFrame, 0), this.totalFrames);
      this.$emit('set-current-frame', Math.round(newCurrentFrame));
    },

    onMouseEvent: function (event) {
      // Set a new playhead position when LMB clicking or dragging.
      if (this.isPlayheadDraggable
        && (event.type === 'mousemove' || event.type === 'mouseup')) {
        const mouse = this.clientToCanvasCoords(event);
        this.setCurrentFrame(mouse.x);
      }

      // Update mouse capturing state.
      if (event.type === 'mousedown') {
        this.isPlayheadDraggable = true;
      } else if (event.type === 'mouseup' || event.type === 'mouseleave') {
        this.isPlayheadDraggable = false;
      }
    },
  }
}

</script>

<style scoped>
  canvas { display:block; }

  #canvas-timeline-container {
    position: relative;
  }
  #canvas-timeline {
    position: absolute;
  }
  #canvas-timeline-text {
    position: absolute;
    z-index: 10;
  }
</style>
