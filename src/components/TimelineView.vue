<template>
  <div id="canvas-timeline-container">
    <canvas id="canvas-timeline"
      @mousedown="onMouseEvent($event)"
      @mouseup="onMouseEvent($event)"
      @mousemove="onMouseEvent($event)"
      @mouseleave="onMouseEvent($event)"
    >
    </canvas>
  </div>
</template>

<script>

import {UIRenderer, Rect, loadTexture} from '../shading';

export default {
  name: "TimelineView",
  props: {
    shots: Array,
    currentFrame: Number,
    totalFrames: Number,
  },
  data () {
    return {
      canvas: null,
      isPlayheadDraggable: false,
      uiRenderer: null,
      uiElements: {
        playhead: {
          padY: 8,
          triangle: {width: 16.0, height: 8.0},
          lineWidth: 2.0,
          color: [0.4, 0.4, 0.4, 1.0],
        },
        timeline: {
          pad: {x: 20, y: 25},
          color: [0.0, 0.4, 0.4, 1.0],
        }
      }
    }
  },
  watch: {
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
      this.canvas.height = 100;

      if (shouldDraw) {
        this.draw();
      }
    },

    initCanvas: function () {
      // Create the rendering setup.
      this.canvas = document.getElementById('canvas-timeline');
      this.uiRenderer = new UIRenderer(this.canvas, this.draw);

      // Resize the canvas to fill browser window dynamically
      window.addEventListener('resize', this.resizeCanvas, false);

      // Call the re-size once to trigger the sizing, but avoid drawing because
      // images (if any) haven't been created yet.
      this.resizeCanvas(false);
    },

    draw: function () {

      const ui = this.uiRenderer;
      const rect = this.getCanvasRect();

      // Timeline area
      const timeline = this.uiElements.timeline;
      const timelineX = timeline.pad.x;
      const timelineY = timeline.pad.y;
      const timelineW = rect.width - timeline.pad.x * 2.0;
      const timelineH = rect.height - timeline.pad.y * 2.0;
      ui.addRect(timelineX, timelineY, timelineW, timelineH, timeline.color);

      // Draw shots
      const shotTop = timelineY + 1;
      const shotHeight = timelineH - 2;
      for (const shot of this.shots) {
        const startPos = timelineX + shot.startFrame * timelineW / this.totalFrames;
        const endFrame = shot.startFrame + shot.durationSeconds * 24;
        const endPos = timelineX + endFrame * timelineW / this.totalFrames;
        ui.addFrame(startPos, shotTop, endPos - startPos, shotHeight, 1,[0.2, 0.3, 0.3, 1.0], 3);
      }

      // Playhead
      // Update the playhead position according to the current frame.
      const playheadPos = timelineX + this.currentFrame * timelineW / this.totalFrames;
      const playhead = this.uiElements.playhead;
      const triangle = this.uiElements.playhead.triangle;
      ui.addLine(
        [playheadPos, playhead.padY + triangle.height], // Triangle tip. (Up)
        [playheadPos, rect.height - playhead.padY], // (Down)
        playhead.lineWidth, playhead.color
      );
      ui.addTriangle(
        [playheadPos                       , playhead.padY + triangle.height], // Center, down.
        [playheadPos - triangle.width * 0.5, playhead.padY], // Top, left.
        [playheadPos + triangle.width * 0.5, playhead.padY], // Top, right.
        playhead.color
      );

      // Draw the frame.
      ui.draw();
    },

    setCurrentFrame: function (canvasX) {
      const rect = this.getCanvasRect();
      const pad = this.uiElements.timeline.pad;
      const timelineRect = new Rect(pad.x, pad.y, rect.width - pad.x * 2.0, rect.height - pad.y * 2.0);
      let newCurrentFrame = (canvasX - timelineRect.left) / timelineRect.width * this.totalFrames;
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
</style>
