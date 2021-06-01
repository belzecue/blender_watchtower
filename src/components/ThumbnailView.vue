<template>
    <div id="canvas-thumb-grid-container">
      <select v-model="displayMode" class="ml-4 mt-2">
        <option value="chronological">Chronological</option>
        <option value="groupByScene">By Scene</option>
      </select>
      <canvas id="canvas-thumb-grid"></canvas>
      <canvas id="canvas-thumb-grid-text"
        @mousedown="onMouseEvent($event)"
        @mouseup="onMouseEvent($event)"
        @mousemove="onMouseEvent($event)"
        @mouseleave="onMouseEvent($event)"
      >
      </canvas>
    </div>
</template>

<script>

import {UIRenderer} from '../shading';

export default {
  name: "ThumbnailView",
  props: {
    scenes: Array,
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
        // View.
        minMargin: 40, // Minimum padding, in pixels, around the thumbnail area. Divide by 2 for one side.
        totalSpacing: [150, 150], // Maximum accumulated space between thumbs + margin.
        // Grouped view.
        thumbGroups: [],
        groupedView: {
          title: { fontSize: 12, spaceBefore: 4, spaceAfter: 2, },
          colorRect: { width: 6, xOffset: 12, },
          minSpacingBetweenThumbs: 2,
        },
      },
      isMouseDragging: false,
      thumbForCurrentFrame: null,
    }
  },
  watch: {
    scenes: function () {
      this.layout();
      this.draw();
    },
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

      // If the resulting layout makes the images too small, skip rendering.
      let hasProblemMsg = null;
      const thumbSize = this.uiElements.thumbnailSize;
      if (!this.shots.length) {
        hasProblemMsg = "No shots loaded";
      } else if (thumbSize[0] <= 5 || thumbSize[1] <= 5) {
        hasProblemMsg = "Out of space";
      }

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
            thumbSize[0] + growSize * 2,
            thumbSize[1] + growSize * 2,
            this.uiElements.thumbTexBundleID, i++
          );
        }
      }

      // Setup style for the text rendering in the overlaid canvas for text.
      this.ui2D.clearRect(0, 0, this.canvasText.width, this.canvasText.height);
      this.ui2D.fillStyle = "rgb(220, 220, 220)";
      this.ui2D.font = "12px sans-serif";
      this.ui2D.textAlign = "left";
      this.ui2D.textBaseline = "top";
      this.ui2D.shadowOffsetX = 2;
      this.ui2D.shadowOffsetY = 2;
      this.ui2D.shadowBlur = 2;
      this.ui2D.shadowColor = 'rgba(0, 0, 0, 0.5)';

      if (hasProblemMsg) {
        // Show a user message indicating why the view is empty
        this.ui2D.textAlign = "center";
        this.ui2D.textBaseline = "middle";
        this.ui2D.fillText(hasProblemMsg, this.canvasText.width * 0.5, this.canvasText.height * 0.5);
      } else if (this.displayMode !== "chronological") {
        // Draw each group.
        for (const group of this.uiElements.thumbGroups) {
          // Draw color rect.
          ui.addRect(group.colorRect[0], group.colorRect[1], group.colorRect[2], group.colorRect[3], group.color, 1);
          // Draw group name.
          this.ui2D.fillText(group.name, group.namePos[0], group.namePos[1]);
        }
      }

      // Draw the frame.
      ui.draw();
    },

    layout: function () {
      console.log("Thumbnail View: Layout");

      // If there are no images to fit, we're done!
      if (!this.shots.length)
        return;

      if (this.displayMode === "chronological")
        this.fitThumbsInGrid();
      else
        this.fitThumbsInGroup();
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
      const spaceW = calculateSpacingCentered(totalAvailableW, thumbnailSize[0], numImagesPerRow, minMargin);
      //console.log("Y");
      const spaceH = calculateSpacingCentered(totalAvailableH, thumbnailSize[1], numImagesPerCol, minMargin);

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

    fitThumbsInGroup: function () {

      const numImages = this.shots.length;

      this.uiElements.thumbGroups = [];

      // Create the thumbnail groups.
      for (const scene of this.scenes) {
        let group = new ThumbnailGroup();
        group.name = scene.name;
        group.uuid = scene.uuid;
        group.color = scene.color;
        this.uiElements.thumbGroups.push(group);
      }
      const unassignedGroup = new ThumbnailGroup("Unassigned");

      // Assign shots to groups.
      for (let i = 0; i < this.shots.length; i++) {
        let g = -1;
        for (let j = 0; j < this.scenes.length; j++) {
          if (this.scenes[j].uuid === this.shots[i].scene) {
            g = j;
            break;
          }
        }
        const group = g === -1 ? unassignedGroup : this.uiElements.thumbGroups[g];

        group.shotIDs.push(i);
        this.uiElements.thumbnails[i].groupIdx = g;
        this.uiElements.thumbnails[i].posInGroup = group.shotIDs.length - 1;
      }
      if (unassignedGroup.shotIDs.length) {
        this.uiElements.thumbGroups.push(unassignedGroup);
      }
      const numGroups = this.uiElements.thumbGroups.length;
      //console.log("Assigned", numImages, "shots to", numGroups, "groups");

      // Find the maximum scale at which the thumbnails can be displayed.

      // Get the distribution of shots per group, sorted, with highest first.
      let shotsPerGroup = [];
      for (const group of this.uiElements.thumbGroups) {
        shotsPerGroup.push(group.shotIDs.length);
      }
      shotsPerGroup.sort((a, b) => b - a);
      //console.log(shotsPerGroup);

      // Get size of the region containing the thumbnails.
      const rect = this.getCanvasRect();
      const totalAvailableW = rect.width;
      const totalAvailableH = rect.height;
      //console.log("Region w:", totalAvailableW, "h:", totalAvailableH);

      // Get the available size, discounting white space size.
      const titleHeight = this.uiElements.groupedView.title.fontSize
                        + this.uiElements.groupedView.title.spaceBefore
                        + this.uiElements.groupedView.title.spaceAfter;
      const colorRectOffset = this.uiElements.groupedView.colorRect.xOffset;
      const colorRectWidth = this.uiElements.groupedView.colorRect.width;
      const minSpacing = this.uiElements.groupedView.minSpacingBetweenThumbs;
      const bothMargins = this.uiElements.minMargin;
      const minSideMargin = bothMargins * 0.5;
      const availableW = totalAvailableW - bothMargins - colorRectOffset;
      const availableH = totalAvailableH - bothMargins - titleHeight * numGroups;

      // Get the original size and aspect ratio of the images.
      // Assume all images in the edit have the same aspect ratio.
      const originalImageW = this.uiElements.originalImageSize[0];
      const originalImageH = this.uiElements.originalImageSize[1];

      // Calculate by how much images need to be scaled in order to fit.

      // Thumbnail images are at their biggest possible size when each group has a single row.
      // Find maximum height and corresponding scale.
      let numImagesPerRow = shotsPerGroup[0];
      let numImagesPerCol = numGroups;
      const maxResY = Math.round((availableH - numImagesPerCol * minSpacing) / numImagesPerCol);
      const heightFitFactor = maxResY / originalImageH;
      // Find a thumbnail width that is guaranteed to fit with all the group's thumbnails in one row.
      const minResX = Math.round((availableW - numImagesPerRow * minSpacing) / numImagesPerRow);
      const rowFitFactor = minResX / originalImageW;

      let scaleFactor = heightFitFactor;

      // If the thumbnails do fit in one row, we're done!
      if (rowFitFactor < heightFitFactor) {
        // Otherwise, do a binary search for the number of columns that maximizes
        // the thumb size (therefore, minimizes scale factor).
        scaleFactor = rowFitFactor;
        let maxCols = shotsPerGroup[0];
        let minCols = 0;
        let checkCols = 1;
        while (maxCols !== checkCols || checkCols !== minCols) {
          checkCols = minCols + Math.ceil((maxCols - minCols) / 2);
          //console.log("check", checkCols, "[", minCols, maxCols, "]");

          // Calculate resulting number of rows, if there are checkCols number of columns.
          let numRows = 0;
          for (const n of shotsPerGroup) {
            numRows += Math.ceil(n / checkCols);
          }
          // Get the scale factor necessary to fit the thumbnails in width and in height.
          // The thumbnails would need to be scaled by the smallest factor to fit in both directions.
          const checkFitFactorW = Math.round((availableW - numImagesPerRow * minSpacing) / checkCols) / originalImageW;
          const checkFitFactorH = Math.round((availableH - numImagesPerCol * minSpacing) / numRows) / originalImageH;
          const checkFitFactor = Math.min(checkFitFactorW, checkFitFactorH);
          //console.log("Checking (", checkCols, "cols,", numRows, "rows). Scale factors:", checkFitFactorW, checkFitFactorH);

          // If the current number of columns gives bigger thumbnails, keep increasing the columns.
          //console.log("check factor:", checkFitFactor, ">= best factor:", scaleFactor);
          if (checkFitFactor >= scaleFactor) {
            scaleFactor = checkFitFactor;
            numImagesPerRow = checkCols;
            numImagesPerCol = numRows;

            if (minCols === checkCols) {
              break;
            } else {
              minCols = checkCols;
            }
          } else {
            // If it is not a better scale factor, search the other direction.
            if (maxCols === checkCols) {
              break;
            } else {
              maxCols = checkCols - 1;
            }
          }
        }
      }
      //console.log("[", numImagesPerRow, "cols x", numImagesPerCol, "rows]. Scale factor:", scaleFactor);

      const thumbSize = [originalImageW * scaleFactor, originalImageH * scaleFactor];
      this.uiElements.thumbnailSize = thumbSize;

      //console.log("X");
      const usableW = totalAvailableW  - colorRectOffset;
      const spaceW = calculateSpacingTopLeftFlow(usableW, thumbSize[0], numImagesPerRow, minSideMargin);
      //console.log("Y");
      const usableH = totalAvailableH  - titleHeight * numGroups;
      const spaceH = calculateSpacingTopLeftFlow(usableH, thumbSize[1], numImagesPerCol, minSideMargin);

      // Set the position of each thumbnail.
      let startPosX = minSideMargin + colorRectOffset;
      let titlePosY = minSideMargin;
      const titleSize = this.uiElements.groupedView.title.fontSize + this.uiElements.groupedView.title.spaceAfter;
      const thumbnailStepX = thumbSize[0] + spaceW;
      const thumbnailStepY = thumbSize[1] + spaceH;

      // Set the position of each group title and colored rectangle.
      for (const group of this.uiElements.thumbGroups) {
        const numShotRows = Math.ceil(group.shotIDs.length / numImagesPerRow);

        // Set the title position and step.
        group.namePos = [startPosX, titlePosY];
        titlePosY += titleHeight + thumbnailStepY * numShotRows;

        // Add total duration and shot count to the group name.
        let durationInSeconds = 0;
        for (const shotID of group.shotIDs) {
          durationInSeconds += this.shots[shotID].durationSeconds;
        }
        group.name += " (shots: " + group.shotIDs.length + ",  " + durationInSeconds.toFixed(1) + "s)";

        // Set the position for the colored rectangle.
        const rectHeight = titleSize + thumbnailStepY * numShotRows;
        const titleTop = group.namePos[1];
        group.colorRect = [
          startPosX - colorRectOffset, titleTop,
          colorRectWidth, rectHeight];
      }

      // Set the position of each thumbnail.
      for (let thumb of this.uiElements.thumbnails) {
        const row = Math.floor(thumb.posInGroup / numImagesPerRow);
        const col = thumb.posInGroup % numImagesPerRow;
        const groupY = this.uiElements.thumbGroups[thumb.groupIdx].namePos[1];
        thumb.pos = [
          startPosX + thumbnailStepX * col,
          groupY + titleSize + thumbnailStepY * row,
        ];
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
function calculateSpacingCentered(totalAvailable, thumbSize, numThumbs, minMargin) {

  const availableSpace = totalAvailable - thumbSize * numThumbs;
  //console.log("remaining space", availableSpace, "px");

  let spacing = 0;
  if (numThumbs > 1) {
    spacing = (availableSpace - minMargin) / (numThumbs - 1);
    //console.log("spacing", spacing);
    // Spacing between images should never be bigger than the margins.
    spacing = Math.min(Math.ceil(spacing), minMargin);
  }

  let margin = (availableSpace - spacing * (numThumbs - 1)) / 2;
  //console.log("margins", margin);
  margin = Math.floor(margin);

  return [margin, spacing];
}

// Get the remaining space not occupied by thumbnails and split it into spacing
// between the thumbnails. Margins are fixed on the top-left.
function calculateSpacingTopLeftFlow(usableSpace, thumbSize, numThumbs, minSideMargin) {

  const remainingSpace = usableSpace - thumbSize * numThumbs - minSideMargin * 2;
  //console.log("remaining space", remainingSpace, "px");

  let spacing = 0;
  if (numThumbs > 1) {
    spacing = Math.round(remainingSpace / (numThumbs - 1));
    //console.log("spacing", spacing);
    // Spacing between images should never be bigger than the margins.
    spacing = Math.min(spacing, minSideMargin);
    // Or disproportionate to the thumbnail size.
    spacing = Math.min(spacing, Math.floor(thumbSize / 5));
    //console.log("spacing clamped", spacing);
  }

  return spacing;
}


// UI element specifying how a thumbnail should be drawn.
function ThumbnailImage (shot) {
  this.pos = [0, 0]; // Position in px where the image should be displayed in canvas coordinates.
  this.shot = shot;
  this.groupIdx = -1;
  this.posInGroup = -1;
}

// UI element representing a container of shots, with its own drawable name and a colorful rectangle.
function ThumbnailGroup (displayStr = "") {
  this.name = displayStr;
  this.namePos = [0, 0]; // Position in px where the group name should be displayed in canvas coordinates.
  this.shotIDs = [];
  this.uuid = "";
  this.color = [0, 0, 0, 1];
  this.colorRect = [0, 0, 0, 0];
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
