<template>
  <div id="canvas-thumb-grid-container" class="column">
    <canvas id="canvas-thumb-grid"
      @mousedown="onMouseEvent($event)"
      @mouseup="onMouseEvent($event)"
      @mousemove="onMouseEvent($event)"
      @mouseleave="onMouseEvent($event)"
    >
    </canvas>
  </div>
</template>

<script>

import { init_shader_program, bind_attr, loadTexture } from './../shading.js';

export default {
  name: "ThumbnailView",
  props: {
    shots: Array,
    currentFrame: Number,
  },
  data () {
    return {
      canvas: null,
      gl: null,
      shaderProgramInfo: null,
      buffers: null,
      uiElements: {
        originalImageSize: [0,0],
        thumbnailSize: [0,0],
        thumbnails: [],
        minMargin: 40, // Minimum padding, in pixels, around the thumbnail area.
        totalSpacing: [150, 150], // Maximum accumulated space between thumbs + margin.
      },
      isMouseDragging: false,
      thumbforCurrentFrame: null,
      frog: null,
    }
  },
  watch: {
    shots: function () {
      console.log("Thumbnail View: Loading " + this.shots.length + " shots")

      if (this.shots.length) {
        this.uiElements.originalImageSize = [1920, 1080]; // 249. 140 // WIP

        for (const shot of this.shots) {
          //const glTextureID = loadTexture(this.gl, shot.thumbnailUrl, this.draw);
          const glTextureID = this.frog;
          this.uiElements.thumbnails.push(new ThumbnailImage(shot, glTextureID));
        }
      }

      this.layout();
      this.draw();
    },
    currentFrame: function () {
      // Find the thumbnail shot that should be highlighted.
      var thumbforCurrentFrame = null;
      for (const thumb of this.uiElements.thumbnails) {
        if(thumb.shot.startFrame > this.currentFrame)
          break;
        thumbforCurrentFrame = thumb;
      }
      this.thumbforCurrentFrame = thumbforCurrentFrame;

      this.draw();
    },
  },
  mounted: function () {
    console.log("Thumbnail View: Initializing...");
    this.initCanvas();
    this.frog = loadTexture(this.gl, "toad.png", this.draw);
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

      this.layout();
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
      const rect = this.getCanvasRect();

      const pixel = {
        x: 2.0 / rect.width, // Shader clip space is [-1,1], therefore divide 2.
        y: 2.0 / rect.height
      }
      const mvp = [1,0,0,0, 0,-1,0,0, 0,0,1,0, 0,0,0,1];
      gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

      // Clear the color buffer with specified clear color
      gl.clear(gl.COLOR_BUFFER_BIT);

      if (this.shots.length)
      {
        gl.useProgram(this.shaderProgramInfo.program);
        gl.uniformMatrix4fv(this.shaderProgramInfo.uniforms.modelViewProj, false, mvp);

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

        for (const thumb of this.uiElements.thumbnails) {

          // Draw the thumbnail for the current frame bigger than the others.
          var growSize = 0;
          if (thumb === this.thumbforCurrentFrame)
              growSize = 5;

          // Bind the data for the shader to use and specify how to interpret it.
          const shaderPadH = pixel.x * (thumb.pos[0] - growSize);
          const shaderPadV = pixel.y * (thumb.pos[1] - growSize);
          const shaderThumbH = pixel.x * (this.uiElements.thumbnailSize[0] + growSize * 2);
          const shaderThumbV = pixel.y * (this.uiElements.thumbnailSize[1] + growSize * 2);
          const positions = new Float32Array([
            -1.0 + shaderPadH + shaderThumbH, -1.0 + shaderPadV + shaderThumbV,
            -1.0 + shaderPadH,                -1.0 + shaderPadV + shaderThumbV,
            -1.0 + shaderPadH + shaderThumbH, -1.0 + shaderPadV,
            -1.0 + shaderPadH,                -1.0 + shaderPadV,
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

          // Bind the texture
          gl.activeTexture(gl.TEXTURE0); // Set context to use TextureUnit 0
          gl.bindTexture(gl.TEXTURE_2D, thumb.glTextureID); // Bind the texture to TextureUnit 0
          gl.uniform1i(this.shaderProgramInfo.uniforms.sampler, 0); // Set shader sampler to use TextureUnit 0

          gl.drawArrays(gl.TRIANGLE_STRIP,
            0, // Offset.
            4  // Vertex count.
          );
        }

        gl.disableVertexAttribArray(this.shaderProgramInfo.attrs.vertexPos);
        gl.disableVertexAttribArray(this.shaderProgramInfo.attrs.texCoord);
        gl.useProgram(null);
      }
    },

    layout: function () {
      console.log("Thumbnail View: Layout");

      // If there are no images to fit, we're done!
      if (!this.shots.length)
        return;

      this.fitThumbsInGrid();
    },

    fitThumbsInGrid: function () {

      const numImages = this.shots.length;

      // Get size of the region containing the thumbnails.
      const rect = this.getCanvasRect();
      const totalAvailableW = rect.width;
      const totalAvailableH = rect.height;
      //console.log(rect);
      //console.log("Region w:", totalAvailableW, "h:", totalAvailableH);

      // Get the available size, discounting white space size.
      const totalSpacing = this.uiElements.totalSpacing;
      const minMargin = this.uiElements.minMargin;
      const availableW = totalAvailableW - totalSpacing[0];
      const availableH = totalAvailableH - totalSpacing[1];
      const maxThumbSize = [totalAvailableW - minMargin, totalAvailableH - minMargin];

      // Get the original size and aspect ratio of the images.
      // Assume all images in the edit have the same aspect ratio.
      const originalImageW = this.uiElements.originalImageSize[0];
      const originalImageH = this.uiElements.originalImageSize[1];
      //console.log("Image a.ratio=", originalImageW / originalImageH, "(", originalImageW, "x", originalImageH,")");

      // Calculate by how much images need to be scaled in order to fit. (won't be perfect)
      const availableArea = availableW * availableH;
      const thumbnailArea = availableArea / numImages;
      // If the pixel area gets very small, early out, not worth rendering.
      if (thumbnailArea < 20) {
        this.uiElements.thumbnailSize = [0,0];
        return
      }
      var scaleFactor = Math.sqrt(thumbnailArea / (originalImageW * originalImageH));
      //console.log("Scale factor:", scaleFactor);

      var thumbnailSize = [originalImageW * scaleFactor, originalImageH * scaleFactor];

      const numImagesPerRow = Math.ceil(availableW / thumbnailSize[0]);
      const numImagesPerCol = Math.ceil(numImages / numImagesPerRow);
      //console.log("Thumbnail width ", thumbnailSize[0], "px, # per row:", numImagesPerRow);
      //console.log("Thumbnail height", thumbnailSize[1], "px, # per col:", numImagesPerCol);

      // Make sure that both a row and a column of images at the current scale will fit.
      // It is possible that, with few images and a region aspect ratio that is very different from
      // the images', there is enough area, but not enough length in one direction.
      // In that case, reduce the thumbnail size further.
      if (originalImageW * scaleFactor * numImagesPerRow > maxThumbSize[0])
        scaleFactor = maxThumbSize[0] / (originalImageW * numImagesPerRow)
      if (originalImageH * scaleFactor * numImagesPerCol > maxThumbSize[1])
        scaleFactor = maxThumbSize[1] / (originalImageH * numImagesPerCol)
      //console.log("Reduced scale factor:", scaleFactor);

      thumbnailSize = [originalImageW * scaleFactor, originalImageH * scaleFactor];
      this.uiElements.thumbnailSize = thumbnailSize

      //console.log("X");
      const spaceW = calculateSpacing(totalAvailableW, thumbnailSize[0], numImagesPerRow, minMargin);
      //console.log("Y");
      const spaceH = calculateSpacing(totalAvailableH, thumbnailSize[1], numImagesPerCol, minMargin);

      const margins = [spaceW[0], spaceH[0]];
      const spacing = [spaceW[1], spaceH[1]];

      // Set the position of each thumbnail.
      var startPosX = margins[0];
      var startPosY = margins[1];
      const lastStartPosX = Math.ceil(
        margins[0] + (numImagesPerRow - 1) * (thumbnailSize[0] + spacing[0])
      );

      for (var img of this.uiElements.thumbnails) {
        img.pos = [startPosX, startPosY];
        startPosX += thumbnailSize[0] + spacing[0];
        // Next row
        if (startPosX > lastStartPosX) {
          startPosX = margins[0];
          startPosY += thumbnailSize[1] + spacing[1];
        }
      }
    },

    setCurrentFrame: function (thumb) {
      const newCurrentFrame = thumb.shot.startFrame;
      this.$emit('set-current-frame', newCurrentFrame);
    },

    onMouseEvent: function (event) {
      // Set a new current frame when LMB clicking or dragging.
      if (this.isMouseDragging
        && (event.type === 'mousemove' || event.type === 'mouseup')) {
        // Hit test against each thumbnail
        const mouse = this.clientToCanvasCoords(event);
        const thumbSize = this.uiElements.thumbnailSize;
        for (const thumb of this.uiElements.thumbnails) {

          // Draw the thumbnail for the current frame bigger than the others.
          var growSize = 0;
          if (thumb === this.thumbforCurrentFrame)
              growSize = 5;

          if ( thumb.pos[0] - growSize <= mouse.x && mouse.x <= thumb.pos[0] + thumbSize[0] + growSize * 2
            && thumb.pos[1] - growSize <= mouse.y && mouse.y <= thumb.pos[1] + thumbSize[1] + growSize * 2) {

            this.setCurrentFrame(thumb);
            break;
          }
        }
      }

      // Update mouse capturing state.
      if (event.type === 'mousedown') {
        this.isMouseDragging = true;
      } else if (event.type === 'mouseup' || event.type === 'mouseleave') {
        this.isMouseDragging = false;
      }
    },
  }
}


// Get the remaining space not occupied by thumbnails and split it into margins
// and spacing between the thumbnails.
function calculateSpacing(totalAvailable, thumbSize, numThumbs, minMargin) {

  const availableSpace = totalAvailable - thumbSize * numThumbs;
  //console.log("remaining space", availableSpace, "px");

  var spacing = 0;
  if (numThumbs > 1) {
    spacing = (availableSpace - minMargin) / (numThumbs - 1);
    //console.log("spacing", spacing);
    // Spacing between images should never be bigger than the margins;
    spacing = Math.min(Math.ceil(spacing), minMargin);
  }

  var margin = (availableSpace - spacing * (numThumbs - 1)) / 2;
  //console.log("margins", margin);
  margin = Math.floor(margin);

  return [margin, spacing];
}


function ThumbnailImage (shot, glImageID) {
  this.glTextureID = glImageID; // GL texture ID.
  this.pos = [0, 0]; // Position in px where the image should be displayed in canvas coordinates.
  this.shot = shot;
  this.group_idx = -1;
  this.pos_in_group = -1;
}

</script>

<style scoped>
  canvas { display:block; }
</style>
