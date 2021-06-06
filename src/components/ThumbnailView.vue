<template>
    <div id="canvas-thumb-grid-container">
      <select v-model="filterMode" class="ml-4 mt-2">
        <option value="showAll">All</option>
        <option value="showActiveSequence">Sequence</option>
        <option value="showActiveTaskType">Task Type</option>
      </select>
      <select v-model="displayMode" class="ml-4 mt-2">
        <option value="chronological">Chronological</option>
        <option value="groupBySequence">By Sequence</option>
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
    sequences: Array,
    shots: Array,
    currentFrame: Number,
  },
  data () {
    return {
      filterMode: 'showAll',
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
        selectedHighlight: { width: 1.5, color: [1.0, 0.561, 0.051, 1.0], },
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
      activeSequence: null,
    }
  },
  watch: {
    filterMode: function () {
      this.layout();
      this.draw();
    },
    displayMode: function () {
      this.layout();
      this.draw();
    },
    sequences: function () {
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
        }
        this.uiElements.thumbTexBundleID = this.uiRenderer.loadImageBundle(thumb_urls, thumb_size);
      }

      this.layout();
      this.draw();
    },
    currentFrame: function () {
      // Find the thumbnail that should be highlighted.
      this.findThumbnailForCurrentFrame();

      // Find the shot for the current frame (not necessarily visible as a thumbnail).
      let shotForCurrentFrame = this.shots.length ? this.shots[0] : null;
      for (const shot of this.shots) {
        if(shot.startFrame > this.currentFrame)
          break;
        shotForCurrentFrame = shot;
      }
      // Find the corresponding sequence, if any.
      let currSequence = null;
      if (shotForCurrentFrame) {
        for (const seq of this.sequences) {
          if (seq.id === shotForCurrentFrame.sequence_id) {
            currSequence = seq;
            break;
          }
        }
      }
      const previouslyCurrSequence = this.activeSequence;
      this.activeSequence = currSequence;

      // Re-layout if the change in current scene affects the filtering.
      if (previouslyCurrSequence!== currSequence && this.filterMode === "showActiveSequence") {
        this.layout();
      }

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
      canvasContainer.style.height = window.innerHeight - 400 + "px";
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

      // If the resulting layout makes the images too small, skip rendering.
      let hasProblemMsg = null;
      const thumbSize = this.uiElements.thumbnailSize;
      if (!this.shots.length) {
        hasProblemMsg = "No shots loaded";
      } else if (thumbSize[0] <= 5 || thumbSize[1] <= 5) {
        hasProblemMsg = "Out of space";
      } else if (Number.isNaN(thumbSize[0]) || Number.isNaN(thumbSize[1])) {
        hasProblemMsg = "Missing layout pass";
      } else if (this.filterMode === "showActiveSequence" && !this.activeSequence) {
        hasProblemMsg = "No sequence selected";
      }

      if (hasProblemMsg) {
        // Show a user message indicating why the view is empty
        this.ui2D.textAlign = "center";
        this.ui2D.textBaseline = "middle";
        this.ui2D.fillText(hasProblemMsg, this.canvasText.width * 0.5, this.canvasText.height * 0.5);
        return;
      }

      for (const thumb of this.uiElements.thumbnails) {
        ui.addImageFromBundle(
          thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1],
          this.uiElements.thumbTexBundleID, thumb.shotIdx
        );
      }
      // Draw a border around the thumbnail corresponding to the current frame.
      if (this.thumbForCurrentFrame) {
        const thumb = this.thumbForCurrentFrame;
        const sel = this.uiElements.selectedHighlight;
        ui.addFrame(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], sel.width, sel.color, 1);
      }

      if (this.displayMode !== "chronological") {
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

    filterThumbnails: function () {

      this.uiElements.thumbnails = [];

      // Create a thumbnail for each shot to be shown.
      if (this.filterMode === "showActiveSequence") {
        if (this.activeSequence) {
          // Show the shots associated with the active sequence.
          for (let i = 0; i < this.shots.length; i++) {
            const shot = this.shots[i];
            if (shot.sequence_id === this.activeSequence.id) {
              this.uiElements.thumbnails.push(new ThumbnailImage(shot, i));
            }
          }
        }
      } else {
        // Show all the shots.
        for (let i = 0; i < this.shots.length; i++) {
          this.uiElements.thumbnails.push(new ThumbnailImage(this.shots[i], i));
        }
      }

      // Update the thumbnail that should be highlighted.
      this.findThumbnailForCurrentFrame();
    },

    refreshThumbnailGroups: function () {

      let thumbGroups = [];

      // Create the thumbnail groups.
      for (const sequence of this.sequences) {
        thumbGroups.push(new ThumbnailGroup(sequence.name, sequence.color));
      }
      const unassignedGroup = new ThumbnailGroup("Unassigned");
      thumbGroups.push(unassignedGroup);

      // Assign thumbnails to groups.
      for (let i = 0; i < this.uiElements.thumbnails.length; i++) {
        let g = -1;
        for (let j = 0; j < this.sequences.length; j++) {
          if (this.sequences[j].id === this.uiElements.thumbnails[i].shot.sequence_id) {
            g = j;
            break;
          }
        }
        const group = g === -1 ? unassignedGroup : thumbGroups[g];

        group.thumbIdxs.push(i);
        this.uiElements.thumbnails[i].group = group;
        this.uiElements.thumbnails[i].posInGroup = group.thumbIdxs.length - 1;
      }

      // Filter out empty groups.
      this.uiElements.thumbGroups = [];
      for (const group of thumbGroups) {
        if (group.thumbIdxs.length) {
          this.uiElements.thumbGroups.push(group);
        }
      }
    },

    layout: function () {

      this.filterThumbnails();

      // If there are no images to fit, we're done!
      if (!this.uiElements.thumbnails.length)
        return;

      if (this.displayMode === "chronological") {
        this.fitThumbsInGrid();
      } else {
        this.refreshThumbnailGroups();
        this.fitThumbsInGroup();
      }
    },

    fitThumbsInGrid: function () {

      const numImages = this.uiElements.thumbnails.length;

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

      // Get the original size and aspect ratio of the images.
      // Assume all images in the edit have the same aspect ratio.
      const originalImageW = this.uiElements.originalImageSize[0];
      const originalImageH = this.uiElements.originalImageSize[1];
      //console.log("Image a.ratio=", originalImageW / originalImageH, "(", originalImageW, "x", originalImageH,")");

      // Calculate maximum limit for thumbnail size.
      let maxThumbSize = numImages === 1 ?
          [totalAvailableW - minMargin, totalAvailableH - minMargin]
          : [availableW, availableH];

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

      const numGroups = this.uiElements.thumbGroups.length;
      //console.log("Assigned", numImages, "shots to", numGroups, "groups");

      // Find the maximum scale at which the thumbnails can be displayed.

      // Get the distribution of thumbnails per group, sorted, with highest first.
      let thumbsPerGroup = [];
      for (const group of this.uiElements.thumbGroups) {
        thumbsPerGroup.push(group.thumbIdxs.length);
      }
      thumbsPerGroup.sort((a, b) => b - a);
      //console.log(thumbsPerGroup);

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
      let numImagesPerRow = thumbsPerGroup[0];
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
        let maxCols = thumbsPerGroup[0];
        let minCols = 0;
        let checkCols = 1;
        while (maxCols !== checkCols || checkCols !== minCols) {
          checkCols = minCols + Math.ceil((maxCols - minCols) / 2);
          //console.log("check", checkCols, "[", minCols, maxCols, "]");

          // Calculate resulting number of rows, if there are checkCols number of columns.
          let numRows = 0;
          for (const n of thumbsPerGroup) {
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
        const numThumbRows = Math.ceil(group.thumbIdxs.length / numImagesPerRow);

        // Set the title position and step.
        group.namePos = [startPosX, titlePosY];
        titlePosY += titleHeight + thumbnailStepY * numThumbRows;

        // Add total duration and shot count to the group name.
        let durationInSeconds = 0;
        for (const thumbIdx of group.thumbIdxs) {
          durationInSeconds += this.uiElements.thumbnails[thumbIdx].shot.durationSeconds;
        }
        group.name += " (shots: " + group.thumbIdxs.length + ",  " + durationInSeconds.toFixed(1) + "s)";

        // Set the position for the colored rectangle.
        const rectHeight = titleSize + thumbnailStepY * numThumbRows;
        const titleTop = group.namePos[1];
        group.colorRect = [
          startPosX - colorRectOffset, titleTop,
          colorRectWidth, rectHeight];
      }

      // Set the position of each thumbnail.
      for (let thumb of this.uiElements.thumbnails) {
        const row = Math.floor(thumb.posInGroup / numImagesPerRow);
        const col = thumb.posInGroup % numImagesPerRow;
        const groupY = thumb.group.namePos[1];
        thumb.pos = [
          startPosX + thumbnailStepX * col,
          groupY + titleSize + thumbnailStepY * row,
        ];
      }
    },

    findThumbnailForCurrentFrame: function () {
      let thumbForCurrentFrame = null;
      for (const thumb of this.uiElements.thumbnails) {
        if(thumb.shot.startFrame > this.currentFrame)
          break;
        thumbForCurrentFrame = thumb;
      }
      this.thumbForCurrentFrame = thumbForCurrentFrame;
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
          if ( thumb.pos[0] <= mouse.x && mouse.x <= thumb.pos[0] + thumbSize[0]
            && thumb.pos[1] <= mouse.y && mouse.y <= thumb.pos[1] + thumbSize[1]) {

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

    onVueReload: function () {

    },
  }
}


// Get the remaining space not occupied by thumbnails and split it into margins
// and spacing between the thumbnails.
function calculateSpacingCentered(totalAvailable, thumbSize, numThumbs, minMargin) {

  const availableSpace = totalAvailable - thumbSize * numThumbs;
  //console.log("remaining space", availableSpace, "px =", totalAvailable, "-", thumbSize, "*", numThumbs);

  let spacing = 0;
  if (numThumbs > 1) {
    spacing = (availableSpace - minMargin) / (numThumbs - 1);
    //console.log("spacing", spacing);
    // Spacing between images should never be bigger than the margins.
    spacing = Math.min(Math.ceil(spacing), minMargin);
    //console.log("spacing clamped", spacing);
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
function ThumbnailImage (shot, shotIdx) {
  // Image display
  this.pos = [0, 0]; // Position in px where the image should be displayed in canvas coordinates.
  // Represented shot
  this.shot = shot; // Shot object that this thumbnail represents.
  this.shotIdx = shotIdx; // Index in the shots array.
  // Grouped view
  this.group = null; // Group that this thumbnail belongs to.
  this.posInGroup = -1; // Relative position in the thumbnails of this group.
}

// UI element representing a container of shots, with its own drawable name and a colorful rectangle.
function ThumbnailGroup (displayStr = "", displayColor = [0.8, 0.0, 0.0, 1.0]) {
  // Group title
  this.name = displayStr;
  this.namePos = [0, 0]; // Position in px where the group name should be displayed in canvas coordinates.
  // Group color
  this.color = displayColor;
  this.colorRect = [0, 0, 0, 0];
  // Contained thumbnails
  this.thumbIdxs = []; // Index in the thumbnails array.
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
