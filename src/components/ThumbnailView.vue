<template>
    <div id="canvas-thumb-grid-container">
      <label for="seqFilterMode">Show</label>
      <select v-model="seqFilterMode" class="ml-4 mt-2">
        <option value="showAll">All</option>
        <option value="showActiveSequence">Current Sequence</option>
      </select>

      <select v-model="taskTypeFilter" class="ml-4 mt-2">
        <option value="">No Task Type</option>
        <option v-for="option in taskTypes" :key="option.id" :value="option.id">
          {{ option.name }}
        </option>
      </select>

      <span v-if="taskTypeFilter !== ''" >
        <input type="checkbox" id="showAssignees" v-model="showAssignees">
        <label for="showAssignees">Assignees</label>

        <input type="checkbox" id="showStatuses" v-model="showStatuses">
        <label for="showStatuses">Status</label>
      </span>

      <label for="displayMode">Group by</label>
      <select v-model="displayMode" class="ml-4 mt-2">
        <option value="chronological">Chronological (ungrouped)</option>
        <option value="groupBySequence">Sequence</option>
        <option v-if="taskTypeFilter !== ''" value="groupByTaskStatus">Task Status</option>
        <option v-if="taskTypeFilter !== ''" value="groupByAssignee">Assignee</option>
      </select>

      <span v-if="taskTypeFilter !== ''">
      <label for="debugOpt1">WIP</label>
      <select v-model="debugOpt1" class="ml-4 mt-2">
        <option value="dots">Dots</option>
        <option value="stripes">Stripes</option>
        <option value="rects">Heatmap</option>
      </select>
      </span>

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

import { UIRenderer } from '../shading';

export default {
  name: "ThumbnailView",
  props: {
    taskTypes: Array,
    taskStatuses: Array,
    users: Array,
    sequences: Array,
    shots: Array,
    currentFrame: Number,
  },
  data () {
    return {
      // View user configuration.
      seqFilterMode: 'showAll',
      taskTypeFilter: '',
      showAssignees: true,
      showStatuses: true,
      displayMode: 'chronological',
      debugOpt1: 'dots',
      // Canvas & rendering context.
      canvas: null,
      canvasText: null,
      uiRenderer: null,
      ui2D: null,
      // Runtime state
      // Thumbnail rendering.
      thumbTexBundleID: null, // Rendering context texture ID for the packed thumb images.
      originalImageSize: [0,0], // Resolution of the provided thumbnail images.
      thumbnailSize: [0,0], // Resolution at which to render the thumbnails.
      thumbnails: [], // Display info for the thumbs that should be rendered. List of ThumbnailImage.
      // Grouped view.
      thumbGroups: [], // Display info for groups. List of ThumbnailGroup.
      summaryText: { str: "", pos: [], }, // Heading with aggregated information of the displayed groups.
      // Assignees.
      userTexBundleID: null, // Rendering context texture ID for the packed user avatar images.
      // Interaction.
      isMouseDragging: false,
      // "Current" elements for the playhead position.
      thumbForCurrentFrame: null,
      activeSequence: null,
      // Task & statuses cache.
      currTaskType: null,
    }
  },
  computed: {
    uiConfig: function() {
      // Layout constants.
      return {
        fontSize: 12,
        selectedHighlight: { width: 1.5, color: [1.0, 0.561, 0.051, 1.0], },
        shotOverlayInfo: { textPad: 5, color: [0.11, 0.11, 0.11, 0.8] },
        taskStatus: { radius: 5, offsetX: 5, offsetY: 6, disabledColor: [0.05, 0.05, 0.05, 0.8] },
        assignees: { avatarSize: 32, offsetX: 5, offsetY: 5, spaceInBetween: 2 },
        // View.
        minMargin: 40, // Minimum padding, in pixels, around the thumbnail area. Divide by 2 for one side.
        totalSpacing: [150, 150], // Maximum accumulated space between thumbs + margin.
        // Grouped view.
        groupedView: {
          summaryText: { spaceBefore: -10, spaceAfter: 12, },
          groupTitle: { spaceBefore: 4, spaceAfter: 2, },
          colorRect: { width: 6, xOffset: 12, },
        },
      };
    }
  },
  watch: {
    seqFilterMode: function () {
      this.refreshAndDraw();
    },
    taskTypeFilter: function () {
      // Find task type object and cache it.
      let taskType = null;
      for (const type of this.taskTypes) { // e.g. "Animation"
        if (this.taskTypeFilter === type.id) {
          taskType = type;
          break;
        }
      }
      this.currTaskType = taskType;

      // If there is no selected TaskType, ensure there is no grouping by task status.
      if (!taskType
          && (this.displayMode === 'groupByTaskStatus' || this.displayMode === 'groupByUser')) {
        this.displayMode = (this.seqFilterMode === 'showAll') ? 'chronological' : 'groupBySequence';
      }

      this.refreshAndDraw();
    },
    showAssignees: function () {
      this.refreshAndDraw();
    },
    showStatuses: function () {
      this.refreshAndDraw();
    },
    displayMode: function () {
      this.refreshAndDraw();
    },
    debugOpt1: function () {
      this.draw();
    },
    taskTypes: function () {
      this.refreshAndDraw();
    },
    taskStatuses: function () {
      this.refreshAndDraw();
    },
    users: function () {
      console.log("Thumbnail View: Loading " + this.users.length + " users")

      if (this.users.length) {
        const thumb_size = [48, 48]; // WIP
        let thumb_urls = []
        for (const user of this.users) {
          thumb_urls.push(user.profilePicture);
        }
        this.userTexBundleID = this.uiRenderer.loadImageBundle(thumb_urls, thumb_size);
      }

      this.refreshAndDraw();
    },
    sequences: function () {
      this.refreshAndDraw();
    },
    shots: function () {
      console.log("Thumbnail View: Loading " + this.shots.length + " shots")

      if (this.shots.length) {
        const thumb_size = [150, 100] ; // [1920, 1080];// WIP
        this.originalImageSize = thumb_size;

        let thumb_urls = []
        for (const shot of this.shots) {
          thumb_urls.push(shot.thumbnailUrl);
        }
        this.thumbTexBundleID = this.uiRenderer.loadImageBundle(thumb_urls, thumb_size);
      }

      this.refreshAndDraw();
    },
    currentFrame: function () {
      // Find the thumbnail that should be highlighted.
      this.thumbForCurrentFrame = this.findThumbnailForCurrentFrame();

      // Find the sequence that is active for the current frame.
      const currSequence = this.findSequenceForCurrentFrame();
      const previouslyCurrSequence = this.activeSequence;
      this.activeSequence = currSequence;

      // Re-layout if the change in current scene affects the filtering.
      if (previouslyCurrSequence!== currSequence && this.seqFilterMode === "showActiveSequence") {
        this.refreshAndDraw();
      } else {
        this.draw();
      }
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

    refreshAndDraw: function () {
      this.filterThumbnails();
      this.refreshThumbnailGroups();
      this.layout();
      this.draw();
    },

    draw: function () {
      const ui = this.uiRenderer;
      // Setup style for the text rendering in the overlaid canvas for text.
      const fontSize = this.uiConfig.fontSize;
      this.ui2D.clearRect(0, 0, this.canvasText.width, this.canvasText.height);
      this.ui2D.fillStyle = "rgb(220, 220, 220)";
      this.ui2D.font = fontSize + "px sans-serif";
      this.ui2D.textAlign = "left";
      this.ui2D.textBaseline = "top";
      this.ui2D.shadowOffsetX = 2;
      this.ui2D.shadowOffsetY = 2;
      this.ui2D.shadowBlur = 2;
      this.ui2D.shadowColor = 'rgba(0, 0, 0, 0.5)';

      // If the resulting layout makes the images too small, skip rendering.
      let hasProblemMsg = null;
      const thumbSize = this.thumbnailSize;
      if (!this.shots.length) {
        hasProblemMsg = "No shots loaded";
      } else if (thumbSize[0] <= 5 || thumbSize[1] <= 5) {
        hasProblemMsg = "Out of space";
      } else if (Number.isNaN(thumbSize[0]) || Number.isNaN(thumbSize[1])) {
        hasProblemMsg = "Missing layout pass";
      } else if (this.seqFilterMode === "showActiveSequence" && !this.activeSequence) {
        hasProblemMsg = "No sequence selected";
      }

      if (hasProblemMsg) {
        // Show a user message indicating why the view is empty
        this.ui2D.textAlign = "center";
        this.ui2D.textBaseline = "middle";
        this.ui2D.fillText(hasProblemMsg, this.canvasText.width * 0.5, this.canvasText.height * 0.5);
        return;
      }

      // Draw the thumbnails.
      for (const thumb of this.thumbnails) {
        ui.addImageFromBundle(
          thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1],
          this.thumbTexBundleID, thumb.shotIdx
        );
      }

      // Draw overlaid information for the shots.
      // Check if there is enough space to show shot names
      const shotInfoSpacing = this.uiConfig.shotOverlayInfo.textPad;
      const textHeightOffset = thumbSize[1] - fontSize - shotInfoSpacing;
      const widthForShotName = this.ui2D.measureText("010_0010_A").width + shotInfoSpacing * 2; // Sample shot name
      const widthForExtras =  this.ui2D.measureText(" - 15.5s").width; // Example
      let shotInfoMode = 0;
      if (thumbSize[0] > widthForShotName * 1.1) { shotInfoMode = 1; }
      if (thumbSize[0] > (widthForShotName + widthForExtras)) { shotInfoMode = 2; }
      if (shotInfoMode > 0) {
        for (const thumb of this.thumbnails) {
          const info = thumb.shot.name + (shotInfoMode === 1 ? "" :
              " - " + thumb.shot.durationSeconds.toFixed(1) + "s");

          ui.addRect(
              thumb.pos[0], thumb.pos[1] + textHeightOffset - shotInfoSpacing,
              thumbSize[0], fontSize + shotInfoSpacing * 2,
              this.uiConfig.shotOverlayInfo.color
          );

          this.ui2D.fillText(info, thumb.pos[0] + shotInfoSpacing, thumb.pos[1] + textHeightOffset);
        }
      }

      // Draw task information.
      if (this.taskTypeFilter !== "") {

        // Get the task type. e.g. "Animation".
        const taskType = this.currTaskType;
        if (!taskType) { console.error("Selected task type not found in data."); return; }

        // Draw task statuses.
        if (this.showStatuses) {

          const statusRadius = this.uiConfig.taskStatus.radius;
          const statusOffsetX = this.uiConfig.taskStatus.offsetX;
          const statusOffsetY = this.uiConfig.taskStatus.offsetY;
          const disabledColor = this.uiConfig.taskStatus.disabledColor;

          const shouldDrawStatuses =
            // Draw if the dots are not too big relative to the thumb size.
            ((thumbSize[0] > (statusRadius * 2) * 2) || this.debugOpt1 !== 'dots')
            // Don't draw if the view is grouped by status, since it would be duplicated information.
            && this.displayMode !== "groupByTaskStatus";
          if (shouldDrawStatuses) {
            const offsetW = thumbSize[0] - statusRadius - statusOffsetX;
            const offsetH = thumbSize[1] - statusRadius - statusOffsetY;
            for (const thumb of this.thumbnails) {
              let hasStatusForTask = false;
              // Search if the shot has a status for the current task type.
              for (const taskStatus of thumb.shot.tasks) {
                if (taskStatus.task_type_id === taskType.id) {
                  // It does, get the color for the status of this task.
                  for (const status of this.taskStatuses) { // e.g. "Done"
                    if (taskStatus.task_status_id === status.id) {
                      if (this.debugOpt1 === 'dots') {
                        ui.addCircle([thumb.pos[0] + offsetW, thumb.pos[1] + offsetH], statusRadius, status.color);
                      } else if (this.debugOpt1 === 'stripes') {
                        ui.addRect(thumb.pos[0], thumb.pos[1] + thumbSize[1] - 6, thumbSize[0], 6, status.color);
                      } else {
                        const color = [status.color[0], status.color[1], status.color[2], 0.4];
                        ui.addRect(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], color);
                      }
                      break;
                    }
                  }
                  hasStatusForTask = true;
                  break;
                }
              }
              if (!hasStatusForTask) {
                ui.addRect(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], disabledColor);
              }
            }
          }
        }

        // Draw assignees
        if (this.showAssignees) {

          const avatarSize = this.uiConfig.assignees.avatarSize * (thumbSize[0] / 200);

          const shouldDrawAssignees =
              // Draw if the avatar size measurable and not too big relative to the thumb size.
              (thumbSize[0] > (avatarSize) * 2) && avatarSize > 4;
          if (shouldDrawAssignees) {
            const offsetW = thumbSize[0] - avatarSize - this.uiConfig.assignees.offsetX;
            const offsetH = this.uiConfig.assignees.offsetY;
            const stepX = avatarSize + this.uiConfig.assignees.spaceInBetween;
            for (const thumb of this.thumbnails) {
              // Search if the shot has a status for the current task type.
              for (const taskStatus of thumb.shot.tasks) {
                if (taskStatus.task_type_id === taskType.id) {
                  // It does, get the assignee(s).
                  for (let aIdx = 0; aIdx < taskStatus.assignees.length; aIdx++) {
                    for (let i = 0; i < this.users.length; i++) {
                      if (taskStatus.assignees[aIdx] === this.users[i].id) {
                        ui.addImageFromBundle(
                          thumb.pos[0] + offsetW - aIdx * stepX, thumb.pos[1] + offsetH,
                          avatarSize, avatarSize,
                          this.userTexBundleID, i, avatarSize * 0.5
                        );
                        break;
                      }
                    }
                  }
                  break;
                }
              }
            }
          }
        }
      }

      // Draw a border around the thumbnail corresponding to the current frame.
      if (this.thumbForCurrentFrame) {
        const thumb = this.thumbForCurrentFrame;
        const sel = this.uiConfig.selectedHighlight;
        ui.addFrame(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], sel.width, sel.color, 1);
      }

      // Draw grouping.
      if (this.displayMode !== "chronological") {

        // Draw the aggregated group information.
        if (this.summaryText.str) {
          this.ui2D.fillText(this.summaryText.str, this.summaryText.pos[0], this.summaryText.pos[1]);
        }

        // Draw each group.
        for (const group of this.thumbGroups) {
          // Draw color rect.
          ui.addRect(
            group.colorRect[0], group.colorRect[1], group.colorRect[2], group.colorRect[3],
            group.color, 1
          );
          // Draw group name.
          this.ui2D.fillText(group.name, group.namePos[0], group.namePos[1]);
        }
      }

      // Draw the frame.
      ui.draw();
    },

    filterThumbnails: function () {

      this.thumbnails = [];

      // Create a thumbnail for each shot to be shown.
      if (this.seqFilterMode === "showActiveSequence") {
        if (this.activeSequence) {
          // Show the shots associated with the active sequence.
          for (let i = 0; i < this.shots.length; i++) {
            const shot = this.shots[i];
            if (shot.sequence_id === this.activeSequence.id) {
              this.thumbnails.push(new ThumbnailImage(shot, i));
            }
          }
        }
      } else {
        // Show all the shots.
        for (let i = 0; i < this.shots.length; i++) {
          this.thumbnails.push(new ThumbnailImage(this.shots[i], i));
        }
      }

      // Update the thumbnail that should be highlighted.
      this.thumbForCurrentFrame = this.findThumbnailForCurrentFrame();
    },

    refreshThumbnailGroups: function () {

      // Clear previous data.
      this.thumbGroups = [];
      this.summaryText.str = "";

      if (this.displayMode === "chronological") {
        return;
      }
      const groupBySequence = (this.displayMode === "groupBySequence");
      const groupByStatus = (this.displayMode === "groupByTaskStatus");
      if (!groupBySequence && !this.currTaskType) {
        console.error("Thumbnail View: can't group by task status/assignee when no task is set.");
        return;
      }

      // Create the thumbnail groups.
      let thumbGroups = [];
      const groupObjs =
        groupBySequence ? this.sequences :
        groupByStatus ? this.taskStatuses : this.users;
      for (const obj of groupObjs) {
        thumbGroups.push(new ThumbnailGroup(obj.name, obj.color, obj));
      }
      const unassignedGroup =
        groupBySequence ? new ThumbnailGroup("Unassigned", [0.8, 0.0, 0.0, 1.0]) :
        groupByStatus ? new ThumbnailGroup("No Status", [0.6, 0.6, 0.6, 1.0]) :
          new ThumbnailGroup("Unassigned", [0.6, 0.6, 0.6, 1.0]);

      // Assign thumbnails to groups.
      const shotBelongsToGroup =
        groupBySequence ? ((objToGroupBy, shot) => { return objToGroupBy.id === shot.sequence_id; }) :
        groupByStatus ? ((objToGroupBy, shot) => {
          // Search if the shot has a status for the current task type.
          for (const taskStatus of shot.tasks) {
            if (taskStatus.task_type_id === this.currTaskType.id) {
              // It does. Does the status match the given thumbnail group?
              return (taskStatus.task_status_id === objToGroupBy.id);
            }
          }
          // Shot doesn't have a task status for the given task type.
          return false;
        }) :
          ((objToGroupBy, shot) => {
            // Search if the shot has a status for the current task type.
            for (const taskStatus of shot.tasks) {
              if (taskStatus.task_type_id === this.currTaskType.id) {
                // It does. Does any assignee match the given one?
                for (const assignee of taskStatus.assignees) {
                  if (assignee === objToGroupBy.id) {
                    return true;
                  }
                }
                break;
              }
            }
            // Shot doesn't have a task status or assignee for the given task type.
            return false;
          });
      for (let i = 0; i < this.thumbnails.length; i++) {
        let g = -1;
        for (let j = 0; j < thumbGroups.length; j++) {
          if (shotBelongsToGroup(thumbGroups[j].criteriaObj, this.thumbnails[i].shot)) {
            g = j;
            break;
          }
        }
        const group = g === -1 ? unassignedGroup : thumbGroups[g];

        group.thumbIdxs.push(i);
        this.thumbnails[i].group = group;
        this.thumbnails[i].posInGroup = group.thumbIdxs.length - 1;
      }

      // Filter out empty groups.
      thumbGroups.push(unassignedGroup);
      for (const group of thumbGroups) {
        if (group.thumbIdxs.length) {
          this.thumbGroups.push(group);
        }
      }

      let totalDuration = 0.0;
      let totalShots = 0;
      for (const group of this.thumbGroups) {
        // Add total duration and shot count to the group name.
        let durationInSeconds = 0;
        for (const thumbIdx of group.thumbIdxs) {
          durationInSeconds += this.thumbnails[thumbIdx].shot.durationSeconds;
        }
        group.name += " (shots: " + group.thumbIdxs.length + ",  "
                      + secToStr(durationInSeconds) + ")";

        // Calculate the aggregated stats of the shots in view.
        totalDuration += durationInSeconds;
        totalShots += group.thumbIdxs.length;
      }

      // Set the aggregated display information if there are multiple groups.
      if (this.thumbGroups.length > 1) {
        this.summaryText.str = "Total shots in view: " + totalShots
                             + ", duration: " + secToStr(totalDuration);
      }
    },

    layout: function () {

      // If there are no images to fit, we're done!
      if (!this.thumbnails.length)
        return;

      if (this.displayMode === "chronological") {
        this.fitThumbsInGrid();
      } else {
        this.fitThumbsInGroup();
      }
    },

    fitThumbsInGrid: function () {

      const numImages = this.thumbnails.length;

      // Get size of the region containing the thumbnails.
      const rect = this.getCanvasRect();
      const totalAvailableW = rect.width;
      const totalAvailableH = rect.height;
      //console.log(rect);
      //console.log("Region w:", totalAvailableW, "h:", totalAvailableH);

      // Get the available size, discounting white space size.
      const totalSpacing = this.uiConfig.totalSpacing;
      const minMargin = this.uiConfig.minMargin;
      const availableW = totalAvailableW - totalSpacing[0];
      const availableH = totalAvailableH - totalSpacing[1];

      // Get the original size and aspect ratio of the images.
      // Assume all images in the edit have the same aspect ratio.
      const originalImageW = this.originalImageSize[0];
      const originalImageH = this.originalImageSize[1];
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
        this.uiConfig.thumbnailSize = [0,0];
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
      this.thumbnailSize = thumbnailSize

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

      for (let img of this.thumbnails) {
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

      const numGroups = this.thumbGroups.length;
      //console.log("Assigned", this.thumbnails.length, "shots to", numGroups, "groups");
      if (numGroups === 0) { return; }

      // Find the maximum scale at which the thumbnails can be displayed.

      // Get the distribution of thumbnails per group, sorted, with highest first.
      let thumbsPerGroup = [];
      for (const group of this.thumbGroups) {
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
      const summaryHeight = numGroups <= 1 ? 0.0 :
                            this.uiConfig.fontSize
                          + this.uiConfig.groupedView.summaryText.spaceBefore
                          + this.uiConfig.groupedView.summaryText.spaceAfter;
      const titleHeight = this.uiConfig.fontSize
                        + this.uiConfig.groupedView.groupTitle.spaceBefore
                        + this.uiConfig.groupedView.groupTitle.spaceAfter;
      const colorRectOffset = this.uiConfig.groupedView.colorRect.xOffset;
      const colorRectWidth = this.uiConfig.groupedView.colorRect.width;
      const bothMargins = this.uiConfig.minMargin;
      const minSideMargin = bothMargins * 0.5;
      const availableW = totalAvailableW - bothMargins - colorRectOffset;
      const availableH = totalAvailableH - bothMargins - summaryHeight - titleHeight * numGroups;

      // Get the original size and aspect ratio of the images.
      // Assume all images in the edit have the same aspect ratio.
      const originalImageW = this.originalImageSize[0];
      const originalImageH = this.originalImageSize[1];

      // Calculate by how much images need to be scaled in order to fit.

      // Thumbnail images are at their biggest possible size when each group has a single row.
      // Find maximum height and corresponding scale.
      let numImagesPerRow = thumbsPerGroup[0];
      let numImagesPerCol = numGroups;
      const heightFitFactor = getFitFactor(availableH, numImagesPerCol, originalImageH);
      // Find a thumbnail width that is guaranteed to fit with all the group's thumbnails in one row.
      const rowFitFactor = getFitFactor(availableW, numImagesPerRow, originalImageW);

      // Limit upscaling of the thumbnails to 1.5x.
      const upscaleLimit = 1.4;
      let scaleFactor = Math.min(upscaleLimit, heightFitFactor);

      // If the thumbnails do fit in one row, we're done!
      if (rowFitFactor < heightFitFactor) {
        // Otherwise, do a linear search for the number of columns that maximizes the thumb size.
        // A binary search may fall into a local maximum.
        scaleFactor = Math.min(upscaleLimit, rowFitFactor);
        for (let numCols = thumbsPerGroup[0]; numCols > 0; numCols--) {
          // Calculate resulting number of rows, if there are "cols" number of columns.
          let numRows = 0;
          for (const n of thumbsPerGroup) {
            numRows += Math.ceil(n / numCols);
          }

          // Get the scale factor necessary to fit the thumbnails in width and in height.

          const checkFitFactorW = getFitFactor(availableW, numCols, originalImageW);
          const checkFitFactorH = getFitFactor(availableH, numRows, originalImageH);
          // The thumbnails would need to be scaled by the smallest factor to fit in both directions.
          const checkFitFactor = Math.min(upscaleLimit, checkFitFactorW, checkFitFactorH);
          //console.log("Checking (", numCols, "cols,", numRows, "rows). Scale factors:", checkFitFactorW, checkFitFactorH);

          // If the current number of columns gives bigger thumbnails, save it as current best.
          if (checkFitFactor > scaleFactor) {
            scaleFactor = checkFitFactor;
            numImagesPerRow = numCols;
            numImagesPerCol = numRows;
          }
        }
      }

      const thumbSize = [originalImageW * scaleFactor, originalImageH * scaleFactor];
      this.thumbnailSize = thumbSize;
      //console.log("[", numImagesPerRow, "cols x", numImagesPerCol, "rows]. Scale factor:",
      // scaleFactor, "Thumb size:", thumbSize);

      //console.log("X");
      const usableW = totalAvailableW  - colorRectOffset;
      const spaceW = calculateSpacingTopLeftFlow(usableW, thumbSize[0], numImagesPerRow, minSideMargin);
      //console.log("Y");
      const usableH = totalAvailableH  - titleHeight * numGroups;
      const spaceH = calculateSpacingTopLeftFlow(usableH, thumbSize[1], numImagesPerCol, minSideMargin);

      // Set the positions of the elements to be displayed.

      let startPosX = minSideMargin + colorRectOffset;
      let titlePosY = minSideMargin + summaryHeight;
      const titleSize = this.uiConfig.fontSize + this.uiConfig.groupedView.groupTitle.spaceAfter;
      const thumbnailStepX = thumbSize[0] + spaceW;
      const thumbnailStepY = thumbSize[1] + spaceH;

      // Set the position of the aggregated group information
      if (this.summaryText.str) {
        const posY = minSideMargin + this.uiConfig.groupedView.summaryText.spaceBefore;
        this.summaryText.pos = [minSideMargin, posY];
      }

      // Set the position of each group title and colored rectangle.
      for (const group of this.thumbGroups) {
        const numThumbRows = Math.ceil(group.thumbIdxs.length / numImagesPerRow);

        // Set the title position and step.
        group.namePos = [startPosX, titlePosY];
        titlePosY += titleHeight + thumbnailStepY * numThumbRows;

        // Set the position for the colored rectangle.
        const rectHeight = titleSize + thumbnailStepY * numThumbRows;
        const titleTop = group.namePos[1];
        group.colorRect = [
          startPosX - colorRectOffset, titleTop,
          colorRectWidth, rectHeight];
      }

      // Set the position of each thumbnail.
      for (let thumb of this.thumbnails) {
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
      for (const thumb of this.thumbnails) {
        if(thumb.shot.startFrame > this.currentFrame)
          break;
        thumbForCurrentFrame = thumb;
      }
      return thumbForCurrentFrame;
    },

    findSequenceForCurrentFrame: function () {
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
      return currSequence;
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
        const thumbSize = this.thumbnailSize;
        for (const thumb of this.thumbnails) {
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
  }
}

function secToStr(timeInSeconds) {
  const h = timeInSeconds / 3600;
  const m = (timeInSeconds / 60) % 60;
  const s = Math.round(timeInSeconds % 60);
  let str = "";
  if (h>1) str += h.toFixed(0) + ":";
  str += m.toFixed(0) + ":";
  return str + s.toFixed(0).padStart(2, '0');
}

function getFitFactor(availableSpace, numThumbs, originalImageSize) {
  const res = Math.round(availableSpace / numThumbs);
  // Spacing must be at least 1/10th of the thumbnail size.
  const minSpacing = Math.round(res * 0.1);
  return (res - minSpacing) / originalImageSize;
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
function ThumbnailGroup (displayStr = "", displayColor = [0.8, 0.0, 0.0, 1.0], criteriaObj = null) {
  // Group title
  this.name = displayStr;
  this.namePos = [0, 0]; // Position in px where the group name should be displayed in canvas coordinates.
  // Group color
  this.color = displayColor;
  this.colorRect = [0, 0, 0, 0];
  // Contained thumbnails
  this.thumbIdxs = []; // Index in the thumbnails array.
  // Object that this group represents, e.g. a Sequence, a Task Status, or an Assignee.
  this.criteriaObj = criteriaObj;
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

  label {
    color: #dadada;
    font-size: 0.9em;
    margin-left: 20px;
  }
  input {
    margin-left: 1rem;
    margin-right: -0.8rem;
  }
</style>
