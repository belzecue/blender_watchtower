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

import { init_shader_program, bind_attr } from './../shading.js';

export default {
  name: "TimelineView",
  props: {
    currentFrame: Number,
    totalFrames: Number,
  },
  data () {
    return {
      canvas: null,
      gl: null,
      shaderProgramInfo: null,
      buffers: null,
      isPlayheadDraggable: false,
      uiElements: {
        playhead: {
          posX: 0,
          padY: 8,
          triangle: {width: 16.0, height: 8.0},
          lineWidth: 2.0,
        },
        timeline: {
          pad: {x: 20, y: 25}
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
      this.canvas = document.getElementById('canvas-timeline');

      // Initialize the GL context.
      const gl = this.canvas.getContext('webgl');
      if (!gl) {
        // Only continue if WebGL is available and working.
        alert('Unable to initialize WebGL. Your browser or machine may not support it.');
        return;
      }
      this.gl = gl;

      // Vertex shader.
      const vs_source = `
        attribute vec2 v_pos;
        uniform mat4 mvp;

        void main() {
          gl_Position = mvp * vec4(v_pos, 0.0, 1.0);
        }
      `;

      // Fragment shader.
      const fs_source = `
        uniform highp vec4 fill_color;

        void main() {
          gl_FragColor = fill_color;
        }
      `;

      // Load and compile shaders
      const shaderProgram = init_shader_program(gl, vs_source, fs_source);

      // Collect the shader's attribute locations.
      this.shaderProgramInfo = {
        program: shaderProgram,
        attrs: {
          vertexPos: bind_attr(gl, shaderProgram, 'v_pos'),
        },
        uniforms: {
          modelViewProj: gl.getUniformLocation(shaderProgram, 'mvp'),
          fillColor: gl.getUniformLocation(shaderProgram, 'fill_color'),
        }
      };

      // Generate GPU buffer IDs that will be filled with data later for the shader to use
      const posBuffer = gl.createBuffer();
      const playheadPosBuffer = gl.createBuffer();

      this.buffers = {
        pos: posBuffer,
        playheadPos: playheadPosBuffer
      };

      gl.clearColor(0.18, 0.18, 0.18, 1.0);

      // Resize the canvas to fill browser window dynamically
      window.addEventListener('resize', this.resizeCanvas, false);

      // Call the re-size once to trigger the sizing and initial draw of this component.
      this.resizeCanvas();
    },

    draw: function () {

      const gl = this.gl;

      // UI items layout. Everything in px.
      const rect = this.getCanvasRect();
      const timeline = this.uiElements.timeline;
      const timelineWidth = rect.width - timeline.pad.x * 2.0;
      this.uiElements.playhead.posX = timeline.pad.x + this.currentFrame * timelineWidth / this.totalFrames;

      const dpi = window.devicePixelRatio;
      const pixel = {
        x: 2.0 * dpi / rect.width, // Shader clip space is [-1,1], therefore divide 2.
        y: 2.0 * dpi / rect.height
      }
      const mvp = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1];
      gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

      // Clear the color buffer with specified clear color
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.useProgram(this.shaderProgramInfo.program);
      gl.uniformMatrix4fv(this.shaderProgramInfo.uniforms.modelViewProj, false, mvp);

      // Bind the data for the shader to use and specify how to interpret it.
      const shaderPadH = pixel.x * this.uiElements.timeline.pad.x;
      const shaderPadV = pixel.y * this.uiElements.timeline.pad.y;
      const positions = new Float32Array([
         1.0 - shaderPadH,  1.0 - shaderPadV,
        -1.0 + shaderPadH,  1.0 - shaderPadV,
         1.0 - shaderPadH, -1.0 + shaderPadV,
        -1.0 + shaderPadH, -1.0 + shaderPadV,
      ]);
      gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.pos);
      gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW); // Transfer data to GPU
      gl.enableVertexAttribArray(this.shaderProgramInfo.attrs.vertexPos);
      gl.vertexAttribPointer(
        this.shaderProgramInfo.attrs.vertexPos, // Shader attribute index
        2,         // Number of elements per vertex
        gl.FLOAT,  // Data type of each element
        false,     // Normalized?
        0,         // Stride if data is interleaved
        0          // Pointer offset to start of data
      );

      // Set the color
      gl.uniform4f(this.shaderProgramInfo.uniforms.fillColor, 0.0, 0.4, 0.4, 1.0);

      gl.drawArrays(gl.TRIANGLE_STRIP,
        0, // Offset.
        4  // Vertex count.
      );

      // Bind the playhead position to the position vertex data
      const playhead = this.uiElements.playhead;
      const playheadPosShader = (playhead.posX / rect.width) * 2.0 - 1.0;
      const playheadTopWidthShader = pixel.x * playhead.triangle.width * 0.5;
      const playheadTopHeightShader = pixel.y * playhead.triangle.height;
      const playheadLineWidthShader = pixel.x * playhead.lineWidth * 0.5;
      const playheadHeightPadShader = pixel.y * playhead.padY;
      const playheadVerts = new Float32Array([
          playheadPosShader + playheadTopWidthShader, 1.0 - playheadHeightPadShader,
          playheadPosShader - playheadTopWidthShader, 1.0 - playheadHeightPadShader,
          playheadPosShader + playheadLineWidthShader, 1.0 - playheadHeightPadShader - playheadTopHeightShader,
          playheadPosShader - playheadLineWidthShader, 1.0 - playheadHeightPadShader - playheadTopHeightShader,
          playheadPosShader + playheadLineWidthShader, -1.0 + playheadHeightPadShader,
          playheadPosShader - playheadLineWidthShader, -1.0 + playheadHeightPadShader,
      ]);
      // Upload the buffer data to the GPU memory
      gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.playheadPos);
      gl.bufferData(gl.ARRAY_BUFFER, playheadVerts, gl.STATIC_DRAW); // Transfer data to GPU
      gl.vertexAttribPointer(
        this.shaderProgramInfo.attrs.vertexPos, // Shader attribute index
        2,         // Number of elements per vertex
        gl.FLOAT,  // Data type of each element
        false,     // Normalized?
        0,         // Stride if data is interleaved
        0          // Pointer offset to start of data
      );
      gl.uniform4f(this.shaderProgramInfo.uniforms.fillColor, 0.4, 0.4, 0.4, 1.0);

      gl.drawArrays(gl.TRIANGLE_STRIP,
        0, // Offset.
        6  // Vertex count.
      );

      gl.disableVertexAttribArray(this.shaderProgramInfo.attrs.vertexPos);
      gl.useProgram(null);
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
