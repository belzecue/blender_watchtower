<template>
    <div id="canvas-thumb-grid-container">
      <select v-model="displayMode" class="ml-4 mt-2">
        <option value="chronological">Chronological</option>
        <option value="groupByScene">By Scene</option>
      </select>
      <canvas id="canvas-thumb-grid"
        @mousedown="onMouseEvent($event)"
        @mouseup="onMouseEvent($event)"
        @mousemove="onMouseEvent($event)"
        @mouseleave="onMouseEvent($event)"
      >
      </canvas>
      <canvas id="canvas-thumb-grid-text"></canvas>
    </div>
</template>

<script>

import {UIRenderer} from '../shading';

export default {
  name: "ThumbnailView",
  props: {
    shots: Array,
    currentFrame: Number,
  },
  data () {
    return {
      displayMode: 'chronological',
      canvas: null,
      canvasText: null,
      uiRenderer: null,
      ui2D: null,
      uiElements: {
        originalImageSize: [0,0],
        thumbnailSize: [0,0],
        thumbnails: [],
        thumbTexBundleID: null,
        minMargin: 40, // Minimum padding, in pixels, around the thumbnail area.
        totalSpacing: [150, 150], // Maximum accumulated space between thumbs + margin.
      },
      isMouseDragging: false,
      thumbForCurrentFrame: null,
      frog: null,
    }
  },
  watch: {
    shots: function () {
      console.log("Thumbnail View: Loading " + this.shots.length + " shots")

      if (this.shots.length) {
        const thumb_size = [150, 100] ; // [1920, 1080];// WIP
        this.uiElements.originalImageSize = thumb_size;

        let thumb_urls = []
        for (const shot of this.shots) {
          thumb_urls.push(shot.thumbnailUrl);
          this.uiElements.thumbnails.push(new ThumbnailImage(shot));
        }
        this.uiElements.thumbTexBundleID = this.uiRenderer.loadImageBundle(thumb_urls, thumb_size);
      }

      this.layout();
      this.draw();
    },
    currentFrame: function () {
      // Find the thumbnail shot that should be highlighted.
      let thumbForCurrentFrame = null;
      for (const thumb of this.uiElements.thumbnails) {
        if(thumb.shot.startFrame > this.currentFrame)
          break;
        thumbForCurrentFrame = thumb;
      }
      this.thumbForCurrentFrame = thumbForCurrentFrame;

      this.draw();
    },
  },
  mounted: function () {
    console.log("Thumbnail View: Initializing...");
    this.initCanvas();

    // Note: Image loading, if any, should go here.

    // Initial draw of this component.
    this.layout();
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
      const canvasContainer = document.getElementById('canvas-thumb-grid-container');
      this.canvas.width = canvasContainer.offsetWidth;
      this.canvas.height = window.innerHeight - 400;

      this.canvasText.width = this.canvas.width;
      this.canvasText.height = this.canvas.height;

      if (shouldDraw) {
        this.layout();
        this.draw();
      }
    },

    initCanvas: function () {
      this.canvas = document.getElementById('canvas-thumb-grid');
      this.uiRenderer = new UIRenderer(this.canvas, this.draw);

      this.canvasText = document.getElementById('canvas-thumb-grid-text');
      this.ui2D = this.canvasText.getContext("2d");

      // Resize the canvas to fill browser window dynamically
      window.addEventListener('resize', this.resizeCanvas, false);

      // Call the re-size once to trigger the sizing, but avoid drawing because
      // images (if any) haven't been created yet.
      this.resizeCanvas(false);
    },

    draw: function () {
      const ui = this.uiRenderer;

      if (this.shots.length) {
        let i = 0;
        for (const thumb of this.uiElements.thumbnails) {
          // Draw the thumbnail for the current frame bigger than the others.
          let growSize = 0;
          if (thumb === this.thumbForCurrentFrame)
            growSize = 5;

          ui.addImageFromBundle(
            thumb.pos[0] - growSize,
            thumb.pos[1] - growSize,
            this.uiElements.thumbnailSize[0] + growSize * 2,
            this.uiElements.thumbnailSize[1] + growSize * 2,
            this.uiElements.thumbTexBundleID, i++
          );
        }
      }

      // Setup style for the text rendering in the overlaid canvas for text.
      this.ui2D.clearRect(0, 0, this.canvasText.width, this.canvasText.height);
      this.ui2D.fillStyle = "rgb(220, 220, 220)";
      this.ui2D.font = "13px sans-serif";
      this.ui2D.textBaseline = "top";
      this.ui2D.shadowOffsetX = 2;
      this.ui2D.shadowOffsetY = 2;
      this.ui2D.shadowBlur = 2;
      this.ui2D.shadowColor = 'rgba(0, 0, 0, 0.5)';
      //this.ui2D.fillText("Hello Canvas!", 140, 40);

      // Draw the frame.
      ui.draw();
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
      let scaleFactor = Math.sqrt(thumbnailArea / (originalImageW * originalImageH));
      //console.log("Scale factor:", scaleFactor);

      let thumbnailSize = [originalImageW * scaleFactor, originalImageH * scaleFactor];

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
      let startPosX = margins[0];
      let startPosY = margins[1];
      const lastStartPosX = Math.ceil(
        margins[0] + (numImagesPerRow - 1) * (thumbnailSize[0] + spacing[0])
      );

      for (let img of this.uiElements.thumbnails) {
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
          let growSize = 0;
          if (thumb === this.thumbForCurrentFrame)
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

  let spacing = 0;
  if (numThumbs > 1) {
    spacing = (availableSpace - minMargin) / (numThumbs - 1);
    //console.log("spacing", spacing);
    // Spacing between images should never be bigger than the margins;
    spacing = Math.min(Math.ceil(spacing), minMargin);
  }

  let margin = (availableSpace - spacing * (numThumbs - 1)) / 2;
  //console.log("margins", margin);
  margin = Math.floor(margin);

  return [margin, spacing];
}


function ThumbnailImage (shot) {
  this.pos = [0, 0]; // Position in px where the image should be displayed in canvas coordinates.
  this.shot = shot;
  this.group_idx = -1;
  this.pos_in_group = -1;
}

</script>

<style scoped>
  canvas { display:block; }

  #canvas-thumb-grid-container {
    position: relative;
    background-color: rgb(46, 46, 46);
  }
  #canvas-thumb-grid {
    position: absolute;
  }
  #canvas-thumb-grid-text {
    position: absolute;
    z-index: 10;
  }
</style>
