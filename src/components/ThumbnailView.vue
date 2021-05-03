<template>
  <div id="canvas-thumb-grid-container" class="column">
    <canvas id="canvas-thumb-grid"></canvas>
  </div>
</template>

<script>
export default {
  name: "ThumbnailView",
  mounted: function () {
    initCanvas();
  },
}


function initCanvas() {
  const canvas = document.getElementById('canvas-thumb-grid');
  const canvasContainer = document.getElementById('canvas-thumb-grid-container');

  canvas.width = canvasContainer.offsetWidth;
  canvas.height = window.innerHeight - 200;
  // Resize the canvas to fill browser window dynamically
  window.addEventListener('resize', resizeCanvas, false);

  function resizeCanvas() {
    canvas.width = canvasContainer.offsetWidth;
    canvas.height = window.innerHeight - 200;
    draw(canvas);
  }

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

    draw(gl, program_info, { pos: pos_buffer, tex_coord: tex_coord_buffer }, texture);

  //  requestAnimationFrame(render);
  //}
  //requestAnimationFrame(render);
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


function isPowerOf2(value) {
  return (value & (value - 1)) == 0;
}


// Initialize a texture and load an image.
// When the image finished loading copy it into the texture.
function loadTexture(gl, url) {

  const texture = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, texture);

  // Because image loading is asynchronous,
  // they might take a moment until they are ready.
  // Until then put a single pixel in the texture so we can
  // use it immediately. When the image has finished downloading
  // we'll update the texture with the contents of the image.
  const level = 0;
  const internalFormat = gl.RGBA;
  const width = 1;
  const height = 1;
  const border = 0;
  const srcFormat = gl.RGBA;
  const srcType = gl.UNSIGNED_BYTE;
  const pixel = new Uint8Array([0, 0, 255, 255]);  // opaque blue
  gl.texImage2D(gl.TEXTURE_2D, level, internalFormat,
                width, height, border, srcFormat, srcType,
                pixel);

  const image = new Image();
  image.onload = function() {
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texImage2D(gl.TEXTURE_2D, level, internalFormat,
                  srcFormat, srcType, image);

    // WebGL1 has different requirements for power of 2 images
    // vs non power of 2 images so check if the image is a
    // power of 2 in both dimensions.
    if (isPowerOf2(image.width) && isPowerOf2(image.height)) {
       // Yes, it's a power of 2. Generate mips.
       gl.generateMipmap(gl.TEXTURE_2D);
    } else {
       // No, it's not a power of 2. Turn of mips and set
       // wrapping to clamp to edge
       gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
       gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
       gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    }
  };
  image.src = url;

  return texture;
}


// Get the shader location of an attribute of a shader by name.
function bind_attr(gl, program, attr_name) {
  const attr_idx = gl.getAttribLocation(program, attr_name);
  if (attr_idx == -1)
    console.error("Can not bind attribute'", attr_name, "'for shader.");
  return attr_idx;
}


// Initialize a shader program with th given vertex and fragment shader source code.
function init_shader_program(gl, vs_source, fs_source) {

  const vs = load_shader(gl, gl.VERTEX_SHADER, vs_source);
  const fs = load_shader(gl, gl.FRAGMENT_SHADER, fs_source);

  // Create the shader program
  const program = gl.createProgram();
  gl.attachShader(program, vs);
  gl.attachShader(program, fs);
  gl.linkProgram(program);

  // Check for failure
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    console.error('An error occurred compiling a shader program: ' + gl.getProgramInfoLog(program));
    gl.deleteProgram(program);
    return null;
  }

  return program;
}


// Creates a shader of the given type with the given source code and compiles it.
function load_shader(gl, shader_type, source_code) {

  const shader = gl.createShader(shader_type);

  console.log("Compiling", (shader_type==gl.VERTEX_SHADER)? "Vertex" : "Fragment", "Shader...");

  gl.shaderSource(shader, source_code);
  gl.compileShader(shader);

  // See if it compiled successfully
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    console.error('An error occurred compiling a shader: ' + gl.getShaderInfoLog(shader));
    gl.deleteShader(shader);
    return null;
  }

  return shader;
}


</script>

<style scoped>
  canvas { display:block; }
</style>
