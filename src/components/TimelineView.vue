<template>
  <div id="canvas-timeline-container" class="column">
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

import { UIRenderer } from './../shading.js';

export default {
  name: "TimelineView",
  props: {
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
          posX: 0,
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
    currentFrame: function () {
      this.draw();
    },
  },
  mounted: function () {
    this.initCanvas();
  },
  methods: {
    getCanvasRect: function () {
      return this.canvas.getBoundingClientRect();
    },

    clientToCanvasCoords: function (event) {
      var rect = this.getCanvasRect();
      return {
         x: event.clientX - rect.left,
         y: event.clientY - rect.top
      };
    },

    resizeCanvas: function () {
      const canvasContainer = document.getElementById('canvas-timeline-container');
      this.canvas.width = canvasContainer.offsetWidth;
      this.canvas.height = 100;
      this.draw();
    },

    initCanvas: function () {
      // Create the rendering setup.
      this.canvas = document.getElementById('canvas-timeline');
      this.uiRenderer = new UIRenderer(this.canvas);

      // Resize the canvas to fill browser window dynamically
      window.addEventListener('resize', this.resizeCanvas, false);

      // Call the re-size once to trigger the sizing and initial draw of this component.
      this.resizeCanvas();
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

      // Playhead
      // Update the playhead position according to the current frame.
      this.uiElements.playhead.posX = timelineX + this.currentFrame * timelineW / this.totalFrames;
      const playhead = this.uiElements.playhead;
      const triangle = this.uiElements.playhead.triangle;
      ui.addLine(
        [playhead.posX, playhead.padY + triangle.height], // Triangle tip. (Up)
        [playhead.posX, rect.height - playhead.padY], // (Down)
        playhead.lineWidth, playhead.color
      );
      ui.addTriangle(
        [playhead.posX                       , playhead.padY + triangle.height], // Center, down.
        [playhead.posX - triangle.width * 0.5, playhead.padY], // Top, left.
        [playhead.posX + triangle.width * 0.5, playhead.padY], // Top, right.
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


function Rect (x, y, w, h) {

  this.left   = x;
  this.right  = x + w;
  this.top    = y;
  this.bottom = y + h;
  this.width  = w;
  this.height = h;

  this.contains = function (x, y) {
    return this.left <= x && x <= this.right &&
           this.top  <= y && y <= this.bottom;
  }

  this.widen = function (val) {
    this.left -= val;
    this.top -= val;
    this.width += val * 2.0;
    this.height += val * 2.0;
    this.right = this.left + this.width;
    this.bottom = this.top + this.height;
  }
  this.widened = function (val) {
    return new Rect(this.left - val, this.top - val,
                this.width + val * 2.0, this.height + val * 2.0);
  }

}

</script>

<style scoped>
  canvas { display:block; }
</style>
