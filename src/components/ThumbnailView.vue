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
  mounted: function () {
    initCanvas();
  },
  watch: {
    shots: function () {
      console.log("Loaded " + this.shots.length + " shots")
    }
  }
}


function initCanvas() {
  const canvas = document.getElementById('canvas-thumb-grid');
  const canvasContainer = document.getElementById('canvas-thumb-grid-container');

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
    attribute vec2 v_tex_coord;

    varying highp vec2 tex_coord;

    void main() {
      gl_Position = vec4(v_pos, 0.0, 1.0);
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
  const shader_program = init_shader_program(gl, vs_source, fs_source);

  // Collect the shader's attribute locations.
  const program_info = {
    program: shader_program,
    attrs: {
      vertex_pos: bind_attr(gl, shader_program, 'v_pos'),
      tex_coord: bind_attr(gl, shader_program, 'v_tex_coord'),
    },
    uniforms: {
      sampler: gl.getUniformLocation(shader_program, 'sampler'),
    }
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

  const tex_coords = new Float32Array([
    0.0, 1.0,
    1.0, 1.0,
    1.0, 0.0,
    0.0, 0.0
  ]);
  const tex_coord_buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, tex_coord_buffer);
  gl.bufferData(gl.ARRAY_BUFFER, tex_coords, gl.STATIC_DRAW);

  const texture = loadTexture(gl, 'toad.png');

  // Make the draw call tick
  //var last_timestamp = 0; // Start time in ms
  //function render(timestamp) {
  //  const delta_ms = timestamp - last_timestamp;
  //  last_timestamp = timestamp;

    //draw(gl, program_info, { pos: pos_buffer, tex_coord: tex_coord_buffer }, texture);

  //  requestAnimationFrame(render);
  //}
  //requestAnimationFrame(render);

  canvas.width = canvasContainer.offsetWidth;
  canvas.height = window.innerHeight - 400;
  // Resize the canvas to fill browser window dynamically
  window.addEventListener('resize', resizeCanvas, false);

  function resizeCanvas() {
    canvas.width = canvasContainer.offsetWidth;
    canvas.height = window.innerHeight - 400;
    draw(gl, program_info, { pos: pos_buffer, tex_coord: tex_coord_buffer }, texture);
  }

  draw(gl, program_info, { pos: pos_buffer, tex_coord: tex_coord_buffer }, texture);
}



function draw(gl, program_info, buffers, texture) {

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

  gl.bindBuffer(gl.ARRAY_BUFFER, buffers.tex_coord);
  gl.enableVertexAttribArray(program_info.attrs.tex_coord);
  gl.vertexAttribPointer(
    program_info.attrs.tex_coord, // Shader attribute index
    2,         // Number of elements per vertex
    gl.FLOAT,  // Data type of each element
    false,     // Normalized?
    0,         // Stride if data is interleaved
    0          // Pointer offset to start of data
  );

  // Bind the texture
  gl.activeTexture(gl.TEXTURE0); // Set context to use TextureUnit 0
  gl.bindTexture(gl.TEXTURE_2D, texture); // Bind the texture to TextureUnit 0
  gl.uniform1i(program_info.uniforms.sampler, 0); // Set shader sampler to use TextureUnit 0

  gl.drawArrays(gl.TRIANGLE_STRIP,
    0, // Offset.
    4  // Vertex count.
  );

  gl.disableVertexAttribArray(program_info.attrs.tex_coord);
  gl.disableVertexAttribArray(program_info.attrs.vertex_pos);
  gl.useProgram(null);
}

</script>

<style scoped>
  canvas { display:block; }
</style>
