<template>
    <div id="canvas-thumb-grid-container">

      <select v-model="mode" class="ml-4 mt-2">
        <option value="shots">Shots</option>
        <option value="assets">Assets</option>
      </select>

      <label for="seqFilterMode">Show</label>
      <select v-model="seqFilterMode" class="ml-4 mt-2">
        <option value="showAll">All</option>
        <option value="showActiveSequence">Current Sequence</option>
        <option value="showShotsInTimelineView">Timeline View</option>
      </select>

      <select v-model="taskTypeFilter" class="ml-4 mt-2">
        <option value="">No Task Type</option>
        <option v-for="option in taskTypesForMode" :key="option.id" :value="option.id">
          {{ option.name }}
        </option>
      </select>

      <span v-if="taskTypeFilter !== ''" >
        <input type="checkbox" id="showAssignees" v-model="showAssignees">
        <label for="showAssignees">Assignees</label>

        <input type="checkbox" id="showStatuses" v-model="showStatuses">
        <label for="showStatuses">Status</label>

        <select v-model="statusDispMode" class="ml-4 mt-2" :disabled="showStatuses === false">
          <option value="dots">Dots</option>
          <option value="stripes">Stripes</option>
          <option value="rects">Heatmap</option>
        </select>
      </span>

      <label for="displayMode">Group by</label>
      <select v-model="displayMode" class="ml-4 mt-2">
        <option v-if="mode === 'shots'" value="chronological">Chronological (ungrouped)</option>
        <option v-if="mode === 'assets'" value="chronological">Ungrouped</option>
        <option v-if="mode === 'shots'" value="groupBySequence">Sequence</option>
        <option v-if="mode === 'assets'" value="groupByAssetType">Asset Type</option>
        <option v-if="taskTypeFilter !== ''" value="groupByTaskStatus">Task Status</option>
        <option v-if="taskTypeFilter !== ''" value="groupByAssignee">Assignee</option>
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
    assets: Array,
    assetTypes: Array,
    fps: Number,
    currentFrame: Number,
    timelineVisibleFrames: Array,
    selectedAssets: Array,
  },
  data () {
    return {
      // View user configuration.
      mode: 'shots',
      seqFilterMode: 'showAll',
      taskTypeFilter: '',
      showAssignees: true,
      showStatuses: true,
      displayMode: 'chronological',
      statusDispMode: 'dots',
      // Canvas & rendering context.
      canvas: null,
      canvasText: null,
      uiRenderer: null,
      ui2D: null,
      // Thumbnail rendering.
      shotsTexBundleID: null, // Rendering context texture ID for the packed thumb images for shots.
      shotsOriginalImageSize: [0,0], // Resolution of the provided thumbnail images.
      assetsTexBundleID: null,
      assetsOriginalImageSize: [0,0],
      thumbnailSize: [0,0], // Resolution at which to render the thumbnails.
      thumbnails: [], // Display info for the thumbs that should be rendered. List of ThumbnailImage.
      duplicatedThumbs: [], // Keep track of thumbnails that represent the same shot (because it shows in multiple groups).
      // Grouped view.
      thumbGroups: [], // Display info for groups. List of ThumbnailGroup.
      summaryText: { str: "", pos: [], }, // Heading with aggregated information of the displayed groups.
      // Assignees.
      usersTexBundleID: null, // Rendering context texture ID for the packed user avatar images.
      // Interaction.
      isMouseDragging: false,
      // "Current" elements for the playhead position.
      thumbForCurrentFrame: null,
      activeSequence: null,
      activeShot: null,
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
        currFrameHighlight: { width: 1.5, color: [0.85, 0.8, 0.7, 1.0], },
        castingHighlight: { width: 1.5, color: [0.2, 0.58, 0.8, 1.0], },
        thumbOverlayInfo: { textPad: 5, color: [0.11, 0.11, 0.11, 0.8] },
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
    },
    taskTypesForShots: function() {
      return this.taskTypes.filter(taskType => taskType.for_shots === true);
    },
    taskTypesForAssets: function() {
      return this.taskTypes.filter(taskType => taskType.for_shots === false);
    },
    taskTypesForMode: function() {
      const showShots = (this.mode === 'shots');
      return this.taskTypes.filter(taskType => taskType.for_shots === showShots);
    }
  },
  watch: {
    mode: function () {
      // If there is a selected TaskType, ensure there is a valid task type for this mode.
      if (this.taskTypeFilter !== '') {
        this.taskTypeFilter = (this.mode === 'shots') ? this.taskTypesForShots[0].id : this.taskTypesForAssets[0].id;
      }

      // Remove unsupported options for assets.
      if (this.mode === 'assets') {
        if (this.displayMode === 'groupBySequence') {
          this.displayMode = 'groupByAssetType';
        }
      } else {
        // Remove unsupported options for shots.
        if (this.displayMode === 'groupByAssetType') {
          this.displayMode = 'groupBySequence';
        }
        this.selectedAssets = [];
      }

      this.refreshAndDraw();
    },
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
    statusDispMode: function () {
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
        this.usersTexBundleID = this.uiRenderer.loadImageBundle(thumb_urls, thumb_size);
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
        this.shotsOriginalImageSize = thumb_size;

        let thumb_urls = []
        for (const shot of this.shots) {
          thumb_urls.push(shot.thumbnailUrl);
        }
        this.shotsTexBundleID = this.uiRenderer.loadImageBundle(thumb_urls, thumb_size);
      }

      this.refreshAndDraw();
    },
    assets: function () {
      console.log("Thumbnail View: Loading " + this.assets.length + " assets")

      if (this.assets.length) {
        const thumb_size = [150, 100]; // WIP
        this.assetsOriginalImageSize = thumb_size;

        let thumb_urls = []
        for (const asset of this.assets) {
          thumb_urls.push(asset.thumbnailUrl);
        }
        this.assetsTexBundleID = this.uiRenderer.loadImageBundle(thumb_urls, thumb_size);
      }

      this.refreshAndDraw();
    },
    currentFrame: function () {
      // Find the thumbnail that should be highlighted.
      this.thumbForCurrentFrame = this.findThumbnailForCurrentFrame();

      // Find the shot and sequence that are active for the current frame.
      const previouslyCurrShot = this.activeShot;
      this.activeShot = this.findShotForCurrentFrame();
      const currSequence = this.findSequenceForCurrentFrame();
      const previouslyCurrSequence = this.activeSequence;
      this.activeSequence = currSequence;

      // Re-layout if the change in current scene affects the filtering.
      if (previouslyCurrSequence !== currSequence && this.seqFilterMode === "showActiveSequence") {
        this.refreshAndDraw();
      } else if (previouslyCurrShot !== this.activeShot) {
        // Update current frame or casting highlights.
        this.draw();
      }
    },
    selectedAssets: function () {
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
      if (!this.shots.length && this.mode === 'shots') {
        hasProblemMsg = "No shots loaded";
      } else if (!this.assets.length && this.mode === 'assets') {
        hasProblemMsg = "No assets loaded";
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
        ui.draw();
        return;
      }

      // Draw the thumbnails.
      const imgBundle = (this.mode === 'shots') ? this.shotsTexBundleID : this.assetsTexBundleID;
      for (const thumb of this.thumbnails) {
        ui.addImageFromBundle(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], imgBundle, thumb.objIdx);
      }

      // Draw overlaid information for the shots.
      // Check if there is enough space to show shot names
      const thumbInfoSpacing = this.uiConfig.thumbOverlayInfo.textPad;
      const textHeightOffset = thumbSize[1] - fontSize - thumbInfoSpacing;
      const widthForInfo = thumbSize[0] - (this.ui2D.measureText("..").width + thumbInfoSpacing * 2);
      let infoMode = 0;
      if (this.mode === 'shots') {
        const widthForShotName = this.ui2D.measureText("010_0010_A").width; // Sample shot name
        const widthForExtras =  this.ui2D.measureText(" - 15.5s").width; // Example
        if (widthForInfo > widthForShotName) { infoMode = 1; }
        if (widthForInfo > (widthForShotName + widthForExtras)) { infoMode = 2; }
      } else {
        if (widthForInfo > 0) { infoMode = 3; }
      }
      if (infoMode > 0) {
        for (const thumb of this.thumbnails) {
          let info = thumb.obj.name
            + (this.duplicatedThumbs[thumb.objIdx] ? "**" : "")
            + (infoMode === 2 ? " - " + thumb.obj.durationSeconds.toFixed(1) + "s" : "");
          if (infoMode === 3) {
            const uncroppedInfo = info;
            while (this.ui2D.measureText(info).width > widthForInfo) {
              info = info.slice(0, -1);
            }
            if (info !== uncroppedInfo) {
              info += "..";
            }
          }

          ui.addRect(
              thumb.pos[0], thumb.pos[1] + textHeightOffset - thumbInfoSpacing,
              thumbSize[0], fontSize + thumbInfoSpacing * 2,
              this.uiConfig.thumbOverlayInfo.color
          );

          this.ui2D.fillText(info, thumb.pos[0] + thumbInfoSpacing, thumb.pos[1] + textHeightOffset);
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
          const thumbDotRatio = 0.5; // Maximum amount of the thumbnail size that a dot can cover.

          const shouldDrawStatuses =
            // Draw if the dots are not too big relative to the thumb size.
            ((thumbSize[0] * thumbDotRatio > statusRadius * 2) || this.statusDispMode !== 'dots')
            // Don't draw if the view is grouped by status, since it would be duplicated information.
            && this.displayMode !== "groupByTaskStatus";
          if (shouldDrawStatuses) {
            const offsetW = thumbSize[0] - statusRadius - statusOffsetX;
            const offsetH = thumbSize[1] - statusRadius - statusOffsetY;
            for (const thumb of this.thumbnails) {
              let hasStatusForTask = false;
              // Search if the shot has a status for the current task type.
              for (const taskStatus of thumb.obj.tasks) {
                if (taskStatus.task_type_id === taskType.id) {
                  // It does, get the color for the status of this task.
                  for (const status of this.taskStatuses) { // e.g. "Done"
                    if (taskStatus.task_status_id === status.id) {
                      if (this.statusDispMode === 'dots') {
                        ui.addCircle([thumb.pos[0] + offsetW, thumb.pos[1] + offsetH], statusRadius, status.color);
                      } else if (this.statusDispMode === 'stripes') {
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
              for (const taskStatus of thumb.obj.tasks) {
                if (taskStatus.task_type_id === taskType.id) {
                  // It does, get the assignee(s).
                  for (let aIdx = 0; aIdx < taskStatus.assignees.length; aIdx++) {
                    for (let i = 0; i < this.users.length; i++) {
                      if (taskStatus.assignees[aIdx] === this.users[i].id) {
                        ui.addImageFromBundle(
                          thumb.pos[0] + offsetW - aIdx * stepX, thumb.pos[1] + offsetH,
                          avatarSize, avatarSize,
                          this.usersTexBundleID, i, avatarSize * 0.5
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

      // Draw a border around the thumbnail(s) of assets used in the current shot.
      if (this.mode === 'assets' && this.activeShot) {
        const rim = this.uiConfig.castingHighlight;
        const transp_overlay_color = [rim.color[0], rim.color[1], rim.color[2], 0.4];
        for (const thumb of this.thumbnails) {
          if (thumb.obj.shots.includes(this.activeShot.id)) {
            ui.addRect(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], transp_overlay_color);
            ui.addFrame(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], rim.width, rim.color, 1);
          }
        }
      }

      // Draw a border around the thumbnail(s) corresponding to the current frame.
      if (this.thumbForCurrentFrame) {
        const thumb = this.thumbForCurrentFrame;
        const rim = this.uiConfig.currFrameHighlight;
        if (this.duplicatedThumbs[thumb.objIdx]) {
          for (const dupThumb of this.duplicatedThumbs[thumb.objIdx])
            ui.addFrame(dupThumb.pos[0], dupThumb.pos[1], thumbSize[0], thumbSize[1], rim.width, rim.color, 1);
        } else {
          ui.addFrame(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], rim.width, rim.color, 1);
        }
      }

      // Draw a border around the thumbnail(s) of selected assets.
      if (this.mode === 'assets') {
        const rim = this.uiConfig.selectedHighlight;
        for (const asset of this.selectedAssets) {
          for (const thumb of this.thumbnails) {
            if (thumb.obj.id === asset.id) {
              ui.addFrame(thumb.pos[0], thumb.pos[1], thumbSize[0], thumbSize[1], rim.width, rim.color, 1);
            }
          }
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

    getFilteredShots: function () {
          // Find which shots to filter by.
          let filtered_shots = [];
          if (this.seqFilterMode === "showActiveSequence") {
            // Get the shots associated with the active sequence.
            if (this.activeSequence) {
              for (const shot of this.shots) {
                if (shot.sequence_id === this.activeSequence.id) {
                  filtered_shots.push(shot);
                }
              }
            }
          } else if (this.seqFilterMode === "showShotsInTimelineView") {
            // Get the shots that are visible in the timeline.
            for (const shot of this.shots) {
              const lastShotFrame = shot.startFrame + shot.durationSeconds * this.fps;
              if (lastShotFrame > this.timelineVisibleFrames[0]
                  && shot.startFrame < this.timelineVisibleFrames[1]) {
                filtered_shots.push(shot);
              }
            }
          }
      return filtered_shots;
    },

    filterThumbnails: function () {

      this.thumbnails = [];
      this.duplicatedThumbs = [];

      if (this.mode === 'shots') {

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

      } else { // 'assets'

        if (this.seqFilterMode === 'showAll') {
          // Show all the assets.
          for (let i = 0; i < this.assets.length; i++) {
            this.thumbnails.push(new ThumbnailImage(this.assets[i], i));
          }
        } else {
          // Find which shots to filter by.
          let filtered_shots = this.getFilteredShots();

          // Create a thumbnail for each asset to be shown.
          for (let i = 0; i < this.assets.length; i++) {
            let is_asset_used_in_a_filtered_shot = false;
            for (const shot of filtered_shots) {
              for (const cast_asset of shot.assets) {
                if (this.assets[i].id === cast_asset.asset_id) {
                  is_asset_used_in_a_filtered_shot = true;
                  break;
                }
              }
              if (is_asset_used_in_a_filtered_shot) { break; }
            }
            if (is_asset_used_in_a_filtered_shot) {
              this.thumbnails.push(new ThumbnailImage(this.assets[i], i));
            }
          }

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
      const groupByAssetType = (this.displayMode === "groupByAssetType");
      const groupByStatus = (this.displayMode === "groupByTaskStatus");
      const groupByAssignee = (this.displayMode === "groupByAssignee");
      if ((groupByStatus || groupByAssignee) && !this.currTaskType) {
        console.error("Thumbnail View: can't group by task status/assignee when no task is set.");
        return;
      }

      // Create the thumbnail groups.
      let thumbGroups = [];
      const groupObjs =
        groupBySequence ? this.sequences :
        groupByAssetType ? this.assetTypes :
        groupByStatus ? this.taskStatuses :
        /* groupByAssignee */ this.users;
      for (const obj of groupObjs) {
        thumbGroups.push(new ThumbnailGroup(obj.name, obj.color, obj));
      }
      const unassignedGroup =
        groupBySequence ? new ThumbnailGroup("Unassigned", [0.8, 0.0, 0.0, 1.0]) :
        groupByAssetType ? new ThumbnailGroup("No Type", [0.8, 0.0, 0.0, 1.0]) :
        groupByStatus ? new ThumbnailGroup("No Status", [0.6, 0.6, 0.6, 1.0]) :
        /* groupByAssignee */ new ThumbnailGroup("Unassigned", [0.6, 0.6, 0.6, 1.0]);

      // Assign thumbnails to groups.
      const objBelongsToGroup =
        groupBySequence ? ((objToGroupBy, shot) => { return objToGroupBy.id === shot.sequence_id; }) :
        groupByAssetType ? ((objToGroupBy, asset) => { return objToGroupBy.id === asset.asset_type_id; }) :
        groupByStatus ? ((objToGroupBy, shotOrAsset) => {
          // Search if the shot/asset has a status for the current task type.
          for (const taskStatus of shotOrAsset.tasks) {
            if (taskStatus.task_type_id === this.currTaskType.id) {
              // It does. Does the status match the given thumbnail group?
              return (taskStatus.task_status_id === objToGroupBy.id);
            }
          }
          // Shot/asset doesn't have a task status for the given task type.
          return false;
        }) : /* groupByAssignee */
          ((objToGroupBy, shotOrAsset) => {
            // Search if the shot/asset has a status for the current task type.
            for (const taskStatus of shotOrAsset.tasks) {
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
            // Shot/asset doesn't have a task status or assignee for the given task type.
            return false;
          });
      const numObjs = this.thumbnails.length;
      for (let i = 0; i < numObjs; i++) {
        // Find all the groups that the shot/asset of this thumbnail belongs to.
        let groupsObjBelongsTo = [];
        for (let j = 0; j < thumbGroups.length; j++) {
          if (objBelongsToGroup(thumbGroups[j].criteriaObj, this.thumbnails[i].obj)) {
            groupsObjBelongsTo.push(j);
          }
        }

        // Register the thumbnail to its group.
        const numGroupsObjBelongsTo = groupsObjBelongsTo.length;
        for (let g = numGroupsObjBelongsTo > 0 ? 0 : -1; g < numGroupsObjBelongsTo; g++) {
          const group = g === -1 ? unassignedGroup : thumbGroups[groupsObjBelongsTo[g]];

          let thumbIdx = i;
          if (g >= 1) {
            // Create a duplicate thumbnail if the shot is in multiple groups.
            thumbIdx = this.thumbnails.push(new ThumbnailImage(
              this.thumbnails[i].obj, this.thumbnails[i].objIdx)
            ) - 1;
            if (!this.duplicatedThumbs[this.thumbnails[i].objIdx]) {
              this.duplicatedThumbs[this.thumbnails[i].objIdx] = [this.thumbnails[i]];
            }
            this.duplicatedThumbs[this.thumbnails[i].objIdx].push(this.thumbnails[thumbIdx]);
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
      let totalObjs = 0;
      for (const group of this.thumbGroups) {
        let durationInSeconds = 0;

        if (this.mode === 'shots') {
          // Add total duration and shot count to the group name.
          for (const thumbIdx of group.thumbIdxs) {
            durationInSeconds += this.thumbnails[thumbIdx].obj.durationSeconds;
          }
          group.name += " (shots: " + group.thumbIdxs.length + ",  "
                        + secToStr(durationInSeconds) + ")";
        } else {
          group.name += " (" + group.thumbIdxs.length + ")";
        }

        // Calculate the aggregated stats of the shots/assets in view.
        totalDuration += durationInSeconds;
        totalObjs += group.thumbIdxs.length;
      }

      // Set the aggregated display information if there are multiple groups.
      if (this.thumbGroups.length > 1) {
        this.summaryText.str = (this.mode === 'shots') ?
          "Total shots in view: " + totalObjs + ", duration: " + secToStr(totalDuration) :
          "Total assets in view: " + totalObjs;
      }
    },

    layout: function () {

      // If there are no images to fit, we're done!
      if (!this.thumbnails.length)
        return;

      const originalImageSize = (this.mode === 'shots') ?
        this.shotsOriginalImageSize :
        this.assetsOriginalImageSize;

      if (this.displayMode === "chronological") {
        this.thumbnailSize = fitThumbsInGrid(
          this.thumbnails, originalImageSize, this.uiConfig, this.getCanvasRect());
      } else {
        this.thumbnailSize = fitThumbsInGroup(
          this.summaryText, this.thumbGroups,
          this.thumbnails, originalImageSize, this.uiConfig, this.getCanvasRect());
      }
    },

    findThumbnailForCurrentFrame: function () {
      if (this.mode === 'assets') { return null; }

      let thumbForCurrentFrame = null;
      for (const thumb of this.thumbnails) {
        if(thumb.obj.startFrame > this.currentFrame)
          break;
        thumbForCurrentFrame = thumb;
      }
      return thumbForCurrentFrame;
    },

    findShotForCurrentFrame: function () {
      // Find the shot for the current frame (not necessarily visible as a thumbnail).
      let shotForCurrentFrame = null;
      for (const shot of this.shots) {
        if (shot.startFrame > this.currentFrame) {
          break;
        }
        shotForCurrentFrame = shot;
      }
      return shotForCurrentFrame;
    },

    findSequenceForCurrentFrame: function () {
      // Find the shot for the current frame (not necessarily visible as a thumbnail).
      let shotForCurrentFrame = this.findShotForCurrentFrame();

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

    setCurrentFrame: function (frame) {
      this.$emit('set-current-frame', frame);
    },

    setSelectedAssets: function (assets) {
      this.$emit('set-selected-assets', assets);
    },

    onMouseEvent: function (event) {
      // Set a new current frame when LMB clicking or dragging.
      if (this.isMouseDragging
        && (event.type === 'mousemove' || event.type === 'mouseup')) {
        // Hit test against each thumbnail
        const mouse = this.clientToCanvasCoords(event);
        const thumbSize = this.thumbnailSize;
        let hitThumb = false;
        for (const thumb of this.thumbnails) {
          if ( thumb.pos[0] <= mouse.x && mouse.x <= thumb.pos[0] + thumbSize[0]
            && thumb.pos[1] <= mouse.y && mouse.y <= thumb.pos[1] + thumbSize[1]) {

            hitThumb = true;
            if (this.mode === 'shots') {
              this.setCurrentFrame(thumb.obj.startFrame);
            } else {
              this.setSelectedAssets([thumb.obj]);
            }
            break;
          }
        }

        if (!hitThumb) {
          if (this.mode === 'assets') {
            this.setSelectedAssets([]);
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
