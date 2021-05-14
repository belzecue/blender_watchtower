<template>
  <div id="canvas-thumb-grid-container" class="column">
    <canvas id="canvas-thumb-grid"></canvas>
  </div>
</template>

<script>

import { init_shader_program, bind_attr, loadTexture } from './../shading.js';

export default {
  name: "ThumbnailView",
  props: {
    shots: Array,
  },
  data () {
    return {
      canvas: null,
      gl: null,
      shaderProgramInfo: null,
      buffers: null,
      uiElements: {
      },
      frog: null,
    }
  },
  watch: {
    shots: function () {
      console.log("Thumbnail View: Loaded " + this.shots.length + " shots")
    }
  },
  mounted: function () {
    this.initCanvas();
    this.frog = loadTexture(this.gl, 'toad.png');
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
      const canvasContainer = document.getElementById('canvas-thumb-grid-container');
      this.canvas.width = canvasContainer.offsetWidth;
      this.canvas.height = window.innerHeight - 400;
      this.draw();
    },

    initCanvas: function () {
      this.canvas = document.getElementById('canvas-thumb-grid');

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
        attribute vec2 v_tex_coord;
        uniform mat4 mvp;

        varying highp vec2 tex_coord;

        void main() {
          gl_Position = mvp * vec4(v_pos, 0.0, 1.0);
          tex_coord = v_tex_coord;
        }
      `;

      // Fragment shader.
      const fs_source = `
        uniform sampler2D sampler;
        varying highp vec2 tex_coord;

        void main() {
          gl_FragColor = texture2D(sampler, tex_coord);
        }
      `;

      // Load and compile shaders
      const shaderProgram = init_shader_program(gl, vs_source, fs_source);

      // Collect the shader's attribute locations.
      this.shaderProgramInfo = {
        program: shaderProgram,
        attrs: {
          vertexPos: bind_attr(gl, shaderProgram, 'v_pos'),
          texCoord: bind_attr(gl, shaderProgram, 'v_tex_coord'),
        },
        uniforms: {
          modelViewProj: gl.getUniformLocation(shaderProgram, 'mvp'),
          sampler: gl.getUniformLocation(shaderProgram, 'sampler'),
        }
      };

      // Generate GPU buffer IDs that will be filled with data later for the shader to use
      const posBuffer = gl.createBuffer();
      const texCoordBuffer = gl.createBuffer();

      this.buffers = {
        pos: posBuffer,
        texCoords: texCoordBuffer
      };

      // Upload the texture coordinate data to the GPU
      const texCoords = new Float32Array([
        1.0, 1.0,
        0.0, 1.0,
        1.0, 0.0,
        0.0, 0.0,
      ]);
      gl.bindBuffer(gl.ARRAY_BUFFER, texCoordBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, texCoords, gl.STATIC_DRAW);

      gl.clearColor(0.18, 0.18, 0.18, 1.0);

      // Resize the canvas to fill browser window dynamically
      window.addEventListener('resize', this.resizeCanvas, false);

      // Call the re-size once to trigger the sizing and initial draw of this component.
      this.resizeCanvas();
    },

    draw: function () {

      const gl = this.gl;

      // UI items layout. Everything in px.
      //const rect = this.getCanvasRect();

      /*const dpi = window.devicePixelRatio;
      const pixel = {
        x: 2.0 * dpi / rect.width, // Shader clip space is [-1,1], therefore divide 2.
        y: 2.0 * dpi / rect.height
      }*/
      const mvp = [1,0,0,0, 0,-1,0,0, 0,0,1,0, 0,0,0,1];
      gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

      // Clear the color buffer with specified clear color
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.useProgram(this.shaderProgramInfo.program);
      gl.uniformMatrix4fv(this.shaderProgramInfo.uniforms.modelViewProj, false, mvp);

      // Bind the data for the shader to use and specify how to interpret it.
      const positions = new Float32Array([
         0.7,  0.7,
        -0.7,  0.7,
         0.7, -0.7,
        -0.7, -0.7,
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

      gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.texCoords);
      gl.enableVertexAttribArray(this.shaderProgramInfo.attrs.texCoord);
      gl.vertexAttribPointer(
        this.shaderProgramInfo.attrs.texCoord, // Shader attribute index
        2,         // Number of elements per vertex
        gl.FLOAT,  // Data type of each element
        false,     // Normalized?
        0,         // Stride if data is interleaved
        0          // Pointer offset to start of data
      );

      // Bind the texture
      gl.activeTexture(gl.TEXTURE0); // Set context to use TextureUnit 0
      gl.bindTexture(gl.TEXTURE_2D, this.frog); // Bind the texture to TextureUnit 0
      gl.uniform1i(this.shaderProgramInfo.uniforms.sampler, 0); // Set shader sampler to use TextureUnit 0

      gl.drawArrays(gl.TRIANGLE_STRIP,
        0, // Offset.
        4  // Vertex count.
      );

      gl.disableVertexAttribArray(this.shaderProgramInfo.attrs.vertexPos);
      gl.disableVertexAttribArray(this.shaderProgramInfo.attrs.texCoord);
      gl.useProgram(null);
    },
  }
}

</script>

<style scoped>
  canvas { display:block; }
</style>
