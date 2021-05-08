<template>
  <div id="canvas-timeline-container" class="column">
    <canvas id="canvas-timeline"></canvas>
  </div>
</template>

<script>

import { init_shader_program, bind_attr } from './../shading.js';

export default {
  name: "TimelineView",
  mounted: function () {
    initCanvas();
  },
}


function initCanvas() {
  const canvas = document.getElementById('canvas-timeline');
  const canvasContainer = document.getElementById('canvas-timeline-container');

  // Initialize the GL context.
  const gl = canvas.getContext('webgl');
  if (!gl) {
    // Only continue if WebGL is available and working.
    alert('Unable to initialize WebGL. Your browser or machine may not support it.');
    return;
  }

  // Vertex shader.
  const vs_source = `
    attribute vec2 v_pos;

    void main() {
      gl_Position = vec4(v_pos, 0.0, 1.0);
    }
  `;

  // Fragment shader.
  const fs_source = `
    void main() {
      gl_FragColor = vec4(0.3, 0.0, 0.3, 1.0);
    }
  `;

  // Load and compile shaders
  const shader_program = init_shader_program(gl, vs_source, fs_source);

  // Collect the shader's attribute locations.
  const program_info = {
    program: shader_program,
    attrs: {
      vertex_pos: bind_attr(gl, shader_program, 'v_pos'),
    },
  };

  // Create data for the shader to use
  const positions = new Float32Array([
     0.7,  0.7,
    -0.7,  0.7,
     0.7, -0.7,
    -0.7, -0.7,
  ]);
  // Upload the buffer data to the GPU memory
  const pos_buffer = gl.createBuffer(); // Generate a buffer ID
  gl.bindBuffer(gl.ARRAY_BUFFER, pos_buffer);
  gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW); // Transfer data to GPU

  // Make the draw call tick
  //var last_timestamp = 0; // Start time in ms
  //function render(timestamp) {
  //  const delta_ms = timestamp - last_timestamp;
  //  last_timestamp = timestamp;

    //draw(gl, program_info, { pos: pos_buffer });

  //  requestAnimationFrame(render);
  //}
  //requestAnimationFrame(render);

  canvas.width = canvasContainer.offsetWidth;
  canvas.height = 100;
  // Resize the canvas to fill browser window dynamically
  window.addEventListener('resize', resizeCanvas, false);

  function resizeCanvas() {
    canvas.width = canvasContainer.offsetWidth;
    canvas.height = 100;
    draw(gl, program_info, { pos: pos_buffer });
  }

  draw(gl, program_info, { pos: pos_buffer });
}


function draw(gl, program_info, buffers) {

  // Clear the color buffer with specified clear color
  gl.clearColor(0.18, 0.18, 0.18, 1.0);
  gl.clear(gl.COLOR_BUFFER_BIT);

  gl.useProgram(program_info.program);

  // Bind the data for the shader to use and specify how to interpret it.
  gl.bindBuffer(gl.ARRAY_BUFFER, buffers.pos);
  gl.enableVertexAttribArray(program_info.attrs.vertex_pos);
  gl.vertexAttribPointer(
    program_info.attrs.vertex_pos, // Shader attribute index
    2,         // Number of elements per vertex
    gl.FLOAT,  // Data type of each element
    false,     // Normalized?
    0,         // Stride if data is interleaved
    0          // Pointer offset to start of data
  );

  gl.drawArrays(gl.TRIANGLE_STRIP,
    0, // Offset.
    4  // Vertex count.
  );

  gl.disableVertexAttribArray(program_info.attrs.vertex_pos);
  gl.useProgram(null);
}

</script>

<style scoped>
  canvas { display:block; }
</style>
