<template>
    <div id="canvas-thumb-grid-container">
      <label for="seqFilterMode">Show</label>
      <select v-model="seqFilterMode" class="ml-4 mt-2">
        <option value="showAll">All</option>
        <option value="showActiveSequence">Current Sequence</option>
        <option value="showShotsInTimelineView">Timeline View</option>
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
      <label for="debugOpt1">Show Task Status with</label>
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
import {ThumbnailImage, ThumbnailGroup, fitThumbsInGrid, fitThumbsInGroup} from '../layout';

export default {
  name: "ThumbnailView",
  props: {
    taskTypes: Array,
    taskStatuses: Array,
    users: Array,
    sequences: Array,
    shots: Array,
    currentFrame: Number,
    fps: Number,
    timelineVisibleFrames: Array,
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
      duplicatedThumbs: [], // Keep track of thumbnails that represent the same shot (because it shows in multiple groups).
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
    timelineVisibleFrames: function () {
      if (this.seqFilterMode === "showShotsInTimelineView") {
        this.refreshAndDraw();
      }
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
        const thumb_size = [400, 400]; // WIP
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
      const previouslyCurrShot = this.thumbForCurrentFrame;
      this.thumbForCurrentFrame = this.findThumbnailForCurrentFrame();

      // Find the sequence that is active for the current frame.
      const currSequence = this.findSequenceForCurrentFrame();
      const previouslyCurrSequence = this.activeSequence;
      this.activeSequence = currSequence;

      // Re-layout if the change in current scene affects the filtering.
      if (previouslyCurrSequence !== currSequence && this.seqFilterMode === "showActiveSequence") {
        this.refreshAndDraw();
      } else if (previouslyCurrShot !== this.thumbForCurrentFrame) {
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
          const info = thumb.shot.name
            + (this.duplicatedThumbs[thumb.shotIdx] ? "**" : "")
            + (shotInfoMode === 1 ?
                "" :
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

      // Draw a border around the thumbnail(s) corresponding to the current frame.
      if (this.thumbForCurrentFrame) {
        const thumb = this.thumbForCurrentFrame;
        const sel = this.uiConfig.selectedHighlight;
        if (this.duplicatedThumbs[thumb.shotIdx]) {
          for (const dupThumb of this.duplicatedThumbs[thumb.shotIdx])
            ui.addFrame(dupThumb.pos[0], dupThumb.pos[1], thumbSize[0], thumbSize[1], sel.width, sel.color, 1);
        } else {
          ui.addFrame(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], sel.width, sel.color, 1);
        }
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
      this.duplicatedThumbs = [];

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
      } else if (this.seqFilterMode === "showShotsInTimelineView") {
        // Show only shots that are visible in the timeline.
        for (let i = 0; i < this.shots.length; i++) {
          const shot = this.shots[i];
          const lastShotFrame = shot.startFrame + shot.durationSeconds * this.fps;
          if (lastShotFrame > this.timelineVisibleFrames[0]
          && shot.startFrame < this.timelineVisibleFrames[1]) {
            this.thumbnails.push(new ThumbnailImage(shot, i));
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
      const numShots = this.thumbnails.length;
      for (let i = 0; i < numShots; i++) {
        // Find all the groups that the shot of this thumbnail belongs to.
        let groupsShotBelongsTo = [];
        for (let j = 0; j < thumbGroups.length; j++) {
          if (shotBelongsToGroup(thumbGroups[j].criteriaObj, this.thumbnails[i].shot)) {
            groupsShotBelongsTo.push(j);
          }
        }

        // Register the thumbnail to its group.
        const numGroupsShotBelongsTo = groupsShotBelongsTo.length;
        for (let g = numGroupsShotBelongsTo > 0 ? 0 : -1; g < numGroupsShotBelongsTo; g++) {
          const group = g === -1 ? unassignedGroup : thumbGroups[groupsShotBelongsTo[g]];

          let thumbIdx = i;
          if (g >= 1) {
            // Create a duplicate thumbnail if the shot is in multiple groups.
            thumbIdx = this.thumbnails.push(new ThumbnailImage(
              this.thumbnails[i].shot, this.thumbnails[i].shotIdx)
            ) - 1;
            if (!this.duplicatedThumbs[this.thumbnails[i].shotIdx])
              this.duplicatedThumbs[this.thumbnails[i].shotIdx] = [this.thumbnails[i]];
            this.duplicatedThumbs[this.thumbnails[i].shotIdx].push(this.thumbnails[thumbIdx]);
          }
          group.thumbIdxs.push(thumbIdx);
          this.thumbnails[thumbIdx].group = group;
          this.thumbnails[thumbIdx].posInGroup = group.thumbIdxs.length - 1;
        }
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
        this.thumbnailSize = fitThumbsInGrid(
          this.thumbnails, this.originalImageSize, this.uiConfig, this.getCanvasRect());
      } else {
        this.thumbnailSize = fitThumbsInGroup(
          this.summaryText, this.thumbGroups,
          this.thumbnails, this.originalImageSize, this.uiConfig, this.getCanvasRect());
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
    font-size: 0.83em;
    margin-left: 20px;
  }
  input {
    margin-left: 1rem;
    margin-right: -0.8rem;
  }
</style>
