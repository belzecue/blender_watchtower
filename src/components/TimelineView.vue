<template>
  <div id="canvas-timeline-container" class="column">
    <canvas id="canvas-timeline"
      @mousedown="onMouseEvent($event)"
      @mouseup="onMouseEvent($event)"
      @mousemove="onMouseEvent($event)">
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
      shader_program_info: null,
      buffers: null,
    }
  },
  computed: {
    canvasRect: function () {
      return this.canvas.getBoundingClientRect();
    },
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
    clientToCanvasCoords: function (event) {
      var rect = this.canvasRect;
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

        void main() {
          gl_Position = vec4(v_pos, 0.0, 1.0);
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
      const shader_program = init_shader_program(gl, vs_source, fs_source);

      // Collect the shader's attribute locations.
      this.shader_program_info = {
        program: shader_program,
        attrs: {
          vertex_pos: bind_attr(gl, shader_program, 'v_pos'),
        },
        uniforms: {
          fill_color: gl.getUniformLocation(shader_program, 'fill_color'),
        }
      };

      // Generate GPU buffer IDs that will be filled with data later for the shader to use
      const pos_buffer = gl.createBuffer();
      const playhead_pos_buffer = gl.createBuffer();

      this.buffers = {
        pos: pos_buffer,
        playhead_pos: playhead_pos_buffer
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
      const rect = this.canvasRect;
      const timeline_box = { pad: {x: 20, y: 25} };
      const timeline_width = rect.width - timeline_box.pad.x * 2.0;
      const playhead = { triangle: {width: 16.0, height: 8.0}, line_width: 2.0, pad: {y: 8} };
      const playhead_pos = timeline_box.pad.x + this.currentFrame * timeline_width / this.totalFrames;

      const dpi = window.devicePixelRatio;
      const pixel = {
        x: 2.0 * dpi / rect.width, // Shader clip space is [-1,1], therefore divide 2.
        y: 2.0 * dpi / rect.height
      }
      gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

      // Clear the color buffer with specified clear color
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.useProgram(this.shader_program_info.program);

      // Bind the data for the shader to use and specify how to interpret it.
      const h_pad_shader = pixel.x * timeline_box.pad.x;
      const v_pad_shader = pixel.y * timeline_box.pad.y;
      const positions = new Float32Array([
         1.0 - h_pad_shader,  1.0 - v_pad_shader,
        -1.0 + h_pad_shader,  1.0 - v_pad_shader,
         1.0 - h_pad_shader, -1.0 + v_pad_shader,
        -1.0 + h_pad_shader, -1.0 + v_pad_shader,
      ]);
      gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.pos);
      gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW); // Transfer data to GPU
      gl.enableVertexAttribArray(this.shader_program_info.attrs.vertex_pos);
      gl.vertexAttribPointer(
        this.shader_program_info.attrs.vertex_pos, // Shader attribute index
        2,         // Number of elements per vertex
        gl.FLOAT,  // Data type of each element
        false,     // Normalized?
        0,         // Stride if data is interleaved
        0          // Pointer offset to start of data
      );

      // Set the color
      gl.uniform4f(this.shader_program_info.uniforms.fill_color, 0.0, 0.4, 0.4, 1.0);

      gl.drawArrays(gl.TRIANGLE_STRIP,
        0, // Offset.
        4  // Vertex count.
      );

      // Bind the playhead position to the position vertex data
      const playhead_pos_shader = (playhead_pos / rect.width) * 2.0 - 1.0;
      const playhead_top_width_shader = pixel.x * playhead.triangle.width * 0.5;
      const playhead_top_height_shader = pixel.y * playhead.triangle.height;
      const playhead_line_width_shader = pixel.x * playhead.line_width * 0.5;
      const playhead_v_pad_shader = pixel.y * playhead.pad.y;
      const playhead_position = new Float32Array([
          playhead_pos_shader + playhead_top_width_shader, 1.0 - playhead_v_pad_shader,
          playhead_pos_shader - playhead_top_width_shader, 1.0 - playhead_v_pad_shader,
          playhead_pos_shader + playhead_line_width_shader, 1.0 - playhead_v_pad_shader - playhead_top_height_shader,
          playhead_pos_shader - playhead_line_width_shader, 1.0 - playhead_v_pad_shader - playhead_top_height_shader,
          playhead_pos_shader + playhead_line_width_shader, -1.0 + playhead_v_pad_shader,
          playhead_pos_shader - playhead_line_width_shader, -1.0 + playhead_v_pad_shader,
      ]);
      // Upload the buffer data to the GPU memory
      gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.playhead_pos);
      gl.bufferData(gl.ARRAY_BUFFER, playhead_position, gl.STATIC_DRAW); // Transfer data to GPU
      gl.vertexAttribPointer(
        this.shader_program_info.attrs.vertex_pos, // Shader attribute index
        2,         // Number of elements per vertex
        gl.FLOAT,  // Data type of each element
        false,     // Normalized?
        0,         // Stride if data is interleaved
        0          // Pointer offset to start of data
      );
      gl.uniform4f(this.shader_program_info.uniforms.fill_color, 0.4, 0.4, 0.4, 1.0);

      gl.drawArrays(gl.TRIANGLE_STRIP,
        0, // Offset.
        6  // Vertex count.
      );

      gl.disableVertexAttribArray(this.shader_program_info.attrs.vertex_pos);
      gl.useProgram(null);
    },

    onMouseEvent: function (event) {
      if (event.type === 'mouseup') {
        console.log("hi froggo");
        var mouse = this.clientToCanvasCoords(event);
        console.log(mouse.x, mouse.y);
      }
    },
  }
}

</script>

<style scoped>
  canvas { display:block; }
</style>
