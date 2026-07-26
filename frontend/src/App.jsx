import React, { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import Plotly from "plotly.js-dist-min";
import { Button, Card, FieldTitle } from "./design-system/index.js";

const API_BASE = "http://127.0.0.1:8000";
const round2 = (n) => Math.round(Number(n) * 100) / 100;
const makeRowId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
const csvCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
const FORNMA_STAGES = [
  "Home",
  "Image Registration",
  "Segmentation",
  "Gating",
  "Foci Overlay",
  "NMA",
  "Plot Data",
  "Clustering",
  "Statistics",
  "Tracking",
];
const HOME_SECTIONS = [
  { id: "about", title: "About" },
  { id: "article", title: "Article" },
  { id: "tutorial-registration", title: "Image Registration" },
  { id: "tutorial-segmentation", title: "Segmentation" },
  { id: "tutorial-gating", title: "Gating" },
  { id: "tutorial-foci", title: "Foci Overlay" },
  { id: "tutorial-nma", title: "NMA" },
  { id: "tutorial-plot", title: "Plot Data" },
  { id: "tutorial-clustering", title: "Clustering" },
  { id: "tutorial-statistics", title: "Statistics" },
  { id: "tutorial-tracking", title: "Tracking" },
  { id: "resources", title: "Resources" },
];
const HOME_INTERFACE_TIPS = [
  "forNMA is modular, so each tab can be used as part of a full workflow or on its own, depending on your experiment.",
  "In most modules, you begin by organizing files by condition and by channel, so consistent names and folder structure are important.",
  "Saving path fields tell the software where to write outputs such as previews, tables, figures, and logs.",
  "Tooltips are available throughout the interface and give a quick explanation of what each parameter does.",
  "While a process is running, use the progress indicators and logs to monitor what is happening. If something goes wrong, save the log text or take a screenshot before reporting it.",
];
const HOME_LOAD_IMAGES_GUIDE = [
  "Click Load images to open the table where you describe how your image folders are organized.",
  "Each row represents one experimental condition, such as Control, Treatment, or a specific timepoint group.",
  "Each channel column represents one imaging channel, such as DAPI, GFP, or another marker.",
  "Inside the table, type the condition names in the first column and rename the channel columns so they match your real acquisition channels.",
  "For each cell in the table, use Browse to choose the folder that contains the images for that specific condition and that specific channel.",
  "If you have more than one condition, use Add condition to create new rows. If you have more than one channel, use Add channel to create new columns.",
  "Click Save only after every row and every channel column is filled in. The software checks whether names are missing, duplicated, or pointing to invalid paths.",
  "If the table feels confusing, read it like this: one row = one condition, one channel column = one marker, one folder path = the image sequence for that combination.",
];
const HOME_MODULE_GUIDES = [
  {
    id: "tutorial-registration",
    title: "Image Registration Tutorial",
    intro:
      "Use Image Registration to correct motion within one channel, or to align multiple channels using one channel as the reference. It is most useful when frame-to-frame consistency matters, especially before tracking.",
    whenToUse: [
      "Use it when the image sequence drifted during acquisition or when channels are slightly misaligned over time.",
      "It is especially important before tracking, since misaligned frames can break trajectories.",
      "For each condition, place all timepoint images from one channel in one folder and the corresponding images from the other channel in a separate folder.",
      "The files inside those channel folders must be in the same temporal order, because registration assumes that matching frames appear in the same sequence across folders.",
    ],
    params: [
      ["Load images", "Opens the condition × channel table where you assign one folder for each condition and each channel."],
      ["Condition", "The experimental condition represented by that row."],
      ["Channel name", "The name of each image channel. Rename the columns so they match your acquisition setup before saving the table."],
      ["Path to channel", "The folder that contains the full time sequence for that condition and channel."],
      ["Browse", "Lets you select the folder for a specific condition and channel directly from the table."],
      ["Save", "Checks the table and closes the window only after names and paths are valid."],
      ["Saving path", "Sets the output folder for registered images and logs."],
      ["Reference channel", "The anchor channel used to align the others."],
      ["Other channels to correct", "Optional channels that will be moved to match the reference channel. Leave this empty when registering only one channel over time."],
      ["Crop output (keep common FOV)", "Keeps only the field of view shared by all aligned images."],
      ["Run Registration", "Starts the registration process."],
      ["Stop", "Requests cancellation of the current registration job."],
    ],
    outputs: [
      "A set of output folders containing the registered image sequences.",
      "Registered images aligned to the reference channel.",
      "Execution logs that help document or troubleshoot the run.",
    ],
    notes: [
      "Registration can be slow and may use a large amount of memory.",
      "In the Load images table, every condition must have one valid folder for every channel column.",
      "Before running, double-check that each condition points to the correct folders and that matching frames stay synchronized across channels.",
      "Load images can feel confusing at first because it works with folders, not with individual files. If something looks wrong, check the table structure first.",
    ],
  },
  {
    id: "tutorial-segmentation",
    title: "Segmentation Tutorial",
    intro:
      "Use Segmentation to detect nuclei, cytoplasm, or both compartments, and to measure selected channels against the resulting contours. Cytoplasmic rings and foci remain available as optional measurements.",
    whenToUse: [
      "Use it to generate nuclear masks, cytoplasm masks, or both, with compartment-specific measurements for later steps such as gating, NMA, plotting, and tracking.",
      "For time-lapse experiments, enable the temporal workflow and keep a single image field per folder.",
    ],
    paramGroups: [
      {
        title: "General setup",
        items: [
          ["Load images", "Opens the condition × channel table used to define the full dataset structure."],
          ["Saving path", "Sets the folder where tables, previews, images, and logs will be saved."],
          ["Segmentation Target", "Chooses whether to segment only nuclei, only cytoplasm, or both compartments."],
          ["Nuclear Detection", "When nuclear segmentation is selected, chooses the channel used to find nuclei."],
          ["Cytoplasm Detection", "When cytoplasm segmentation is selected, chooses the channel used to generate whole-cell/cytoplasm masks with Cellpose."],
          ["Overtime", "Marks the dataset as a time sequence. Use this when the folders contain frames from the same field over time."],
          ["Foci", "Turns on foci detection so the software can count spot-like structures in the selected channels."],
          ["Channels for Foci", "Defines which channels should be analyzed for foci detection."],
          ["Cytoplasmatic Ring", "Turns on translocation-style measurements around the nucleus by creating a ring outside the nuclear contour."],
          ["Channels for Cytoplasmatic Ring", "Defines which channels should be used for cytoplasmic ring measurements."],
          ["Magnification", "The microscope magnification used during image acquisition. In the original documentation, this is treated as the only mandatory segmentation value."],
          ["Pixel Size", "The real size of one pixel in micrometers."],
          ["Nuclear Segmentation Method", "Chooses which nuclear segmentation workflow will be used: the native forNMA pipeline or Cellpose. Cytoplasm segmentation uses Cellpose."],
        ],
      },
      {
        title: "Compartment preprocessing and filters",
        items: [
          ["Nuclear / Cytoplasm Segmentation panels", "Each compartment has its own preprocessing and advanced-filter settings. Changing cytoplasm settings does not change nuclear segmentation settings."],
          ["Rescale Intensity", "Redistributes image intensity before segmentation of that compartment and can improve contrast."],
          ["Remove Background", "Applies rolling-ball background subtraction before segmentation of that compartment."],
          ["Rolling Ball Radius", "Defines the size of the rolling-ball background correction for that compartment."],
          ["Shape and Eccentricity", "Optionally filter masks by irregularity or elongation."],
          ["Min / Max Size and Radius", "Optionally restrict the size of accepted nuclear or cytoplasm masks."],
        ],
      },
      {
        title: "forNMA nuclear segmentation",
        items: [
          ["Threshold", "Defines how the software separates nucleus from background in the native forNMA workflow. Global and local threshold options are available."],
          ["Weakly labeled images", "Activates extra routines for images where nuclear staining is weak and the nuclear boundary is hard to identify."],
          ["Find low-intensity nuclei", "Runs an extra search step to detect nuclei that may have been missed in low-intensity regions."],
        ],
      },
      {
        title: "Cellpose nuclear segmentation",
        items: [
          ["Cellpose Model", "Pretrained Cellpose model used for segmentation. For nuclear detection, try `nuclei`, `cyto3`, `cyto2`, or `cyto` depending on the image style."],
          ["Cellpose Diameter", "Expected nucleus diameter, in pixels, used by Cellpose."],
          ["Cellpose Flow Threshold", "Controls the allowed flow error in Cellpose. Objects with errors below the threshold are kept."],
          ["Cellprob Threshold", "Controls the minimum cell probability accepted by Cellpose."],
          ["Use GPU", "Allows Cellpose to run on GPU when one is available."],
          ["Invert Intensities", "Inverts the image intensity before Cellpose segmentation when needed."],
        ],
      },
      {
        title: "Cellpose cytoplasm segmentation",
        items: [
          ["Model", "Pretrained Cellpose model used to create cytoplasm/whole-cell masks. For cells imaged in visible light or brightfield, start with `cyto3`."],
          ["Visible-light / brightfield suggestion", "For visible-light or brightfield cells, we recommend starting with model `cyto3`, increasing Flow Threshold to `0.6`-`0.8`, and reducing Cellprob Threshold to `-3` or `-4`."],
          ["Diameter", "Expected whole-cell diameter, in pixels, used by Cellpose."],
          ["Flow Threshold", "Controls the allowed flow error. Increasing it to `0.6`-`0.8` can help retain valid masks in visible-light cell images."],
          ["Cellprob Threshold", "Controls the minimum cell probability. Lower values such as `-3` or `-4` may help recover visible-light cell masks."],
          ["Invert Intensities", "Inverts image intensity before Cellpose segmentation when needed."],
        ],
      },
      {
        title: "Per-channel detection and measurements",
        items: [
          ["Measure nucleus / Measure cytoplasm", "When both masks are generated, chooses whether each channel is measured inside nuclear contours, cytoplasm contours, or both. Channels measured in both compartments are processed independently."],
          ["Per-channel Rescale intensity", "Applies intensity redistribution independently to one measurement channel."],
          ["Per-channel Remove background", "Applies rolling-ball background correction independently to one measurement channel."],
          ["Per-channel Rolling-ball radius", "Defines the rolling-ball radius for that specific measurement channel."],
          ["Match histograms", "Matches image histograms using the first image as reference, helping correct illumination differences across images."],
          ["Ring size", "Width of the cytoplasmic ring, in pixels, used in translocation measurements."],
          ["Use ellipse", "Uses an ellipse instead of a simple expanded contour to build the cytoplasmic ring. This can help in elongated cell lines."],
          ["Min foci size", "Minimum number of pixels required for a region to be counted as a focus."],
          ["Max foci size", "Maximum number of pixels allowed for a region to still be counted as a focus."],
          ["Min foci intensity", "Minimum mean intensity required for a region to be counted as a focus."],
          ["Max foci intensity", "Maximum mean intensity allowed for a region to be counted as a focus."],
          ["Foci prominence", "How much brighter a focus must be relative to the surrounding nucleus."],
        ],
      },
      {
        title: "Run controls",
        items: [
          ["Preview / Run / Stop", "Preview checks the current setup, Run starts the full process, and Stop requests cancellation."],
        ],
      },
    ],
    outputs: [
      {
        title: "Annotated images",
        description: "forNMA returns image outputs in the results folder so you can visually inspect what was detected.",
        items: [
          "Annotated 8-bit RGB images showing the segmentation and any user-selected measurements.",
          "Preview-style outputs that help you check whether the nuclear contours look correct.",
        ],
      },
      {
        title: "Pickle files (.pkl)",
        description: "These files store structured results that can be reused by downstream tools.",
        items: [
          "A folder containing `.pkl` objects for later use in modules such as Foci Overlay.",
          "If you do not plan to use those downstream analyses, these files are not usually the main results you need to inspect manually.",
        ],
      },
      {
        title: "Nuclei Results CSV",
        description: "This is the per-nucleus results table. For a run that includes cytoplasm segmentation, nuclear measurements are saved separately from cytoplasm measurements.",
        items: [
          "Whenever you see `ChannelName` in a column description, it means the actual channel name you entered in Load images. These columns are created once for each channel. For example, if you define the channels as `Red` and `Green`, columns such as `Mean_ChannelName` will appear in the table as `Mean_Red` and `Mean_Green`.",
          "Frame, Cell, X, Y: identify the image frame, nucleus number, and centroid position.",
          "Area, Perimeter: basic size and boundary measurements of each nucleus.",
          "Aspect, Extent, Roundness, Radius_ratio: shape descriptors used to describe how elongated, compact, or irregular the nucleus is.",
          "NII: the Nuclear Irregularity Index, a combined metric based on aspect, extent, radius ratio, and roundness.",
          "FitEllipse_X, FitEllipse_Y, FitEllipse_a, FitEllipse_b, FitEllipse_angle: parameters of the ellipse fitted to the nucleus.",
          "Image_name_ChannelName, Min_image_ChannelName, Max_image_ChannelName: image identity and image-level intensity range for that channel.",
          "Mean_ChannelName, Median_ChannelName: mean and median intensity measured inside the nucleus for each channel.",
          "Mean_ring_ChannelName, Median_ring_ChannelName: mean and median intensity measured in the cytoplasmic ring region.",
          "Mean_ellipse_ChannelName, Median_ellipse_ChannelName: mean and median intensity measured in the elliptical ring region.",
          "Mean_Ring/Nucleus, Median_Ring/Nucleus, Mean_Nucleus/Ring, Median_Nucleus/Ring: ratios between ring and nuclear intensities.",
          "Mean_Ellipse/Nucleus, Median_Ellipse/Nucleus, Mean_Nucleus/Ellipse, Median_Nucleus/Ellipse: ratios between elliptical ring and nuclear intensities.",
          "Total_foci_ChannelName, Total_foci_area_ChannelName, Total_foci_mean_ChannelName, Foci_area_fraction_ChannelName: summary foci measurements per nucleus when foci detection is enabled.",
          "Condition and Overtime: identify the user-defined condition and whether the dataset belongs to a time series.",
        ],
      },
      {
        title: "Cytoplasm Results CSV",
        description: "When cytoplasm segmentation is selected, this table stores measurements made with cytoplasm contours.",
        items: [
          "Cytoplasmic measurements are kept in their own table so they do not replace or mix with per-nucleus results.",
          "When both compartments are measured, channel-derived columns are identified with the appropriate compartment suffix, such as `_nuc` or `_cyto`.",
        ],
      },
      {
        title: "Nuclei Cytoplasm Mapping CSV",
        description: "When both nucleus and cytoplasm segmentation are selected, this relationship table links objects without duplicating their measurements.",
        items: [
          "Nucleus_ID and Cytoplasm_ID refer to the `Cell` identifiers in the corresponding results tables for the same condition and frame.",
          "Pair_status identifies matched objects, multinucleated cytoplasms, ambiguous assignments, nuclei without cytoplasm, and cytoplasms without a nucleus.",
          "N_nuclei_in_cytoplasm and N_cytoplasms_for_nucleus make multiple or ambiguous relationships explicit before downstream analysis.",
        ],
      },
      {
        title: "Foci Results CSV",
        description: "When foci detection is enabled, forNMA can also return a second CSV with one row per individual focus.",
        items: [
          "Channel, Image_name, Frame: identify where the focus was found.",
          "Origin_nucleus, Focus_number: identify which nucleus the focus belongs to and its index inside that nucleus.",
          "Focus_mean_intensity, Focus_Area, Focus_perimeter: intensity and shape measurements for each focus.",
          "Focus_centroid_x, Focus_centroid_y: focus position in the image.",
          "Condition and Is_overtime: identify the experimental condition and whether the data are part of a time series.",
        ],
      },
      {
        title: "Logs and run information",
        description: "The results folder also includes files that help document the run and troubleshoot problems.",
        items: [
          "Execution logs and intermediate outputs saved in the selected results folder.",
        ],
      },
    ],
    notes: [
      "Load images is the step that defines the whole dataset structure, so mistakes there usually affect everything that comes after.",
    ],
  },
  {
    id: "tutorial-gating",
    title: "Gating Tutorial",
    intro:
      "Use Gating to filter a dataset by applying numeric limits to two selected variables. This is useful for removing debris, extreme outliers, or other unwanted populations before downstream analysis.",
    whenToUse: [
      "Use it when you want to clean a dataset before plotting, statistics, or clustering.",
      "A common approach is to gate area- and shape-related columns to remove obvious segmentation artifacts.",
    ],
    params: [
      ["Datasets", "Load one or more CSV files to filter."],
      ["PKL folder", "Optional folder with segmentation `.pkl` files for each dataset. This is required only if you want the gate to be applied to images as well as to tables."],
      ["X column / Y column", "Select the numeric columns used in the 2D gating view."],
      ["X min / X max / Y min / Y max", "Set the numeric limits for the selected variables."],
      ["q_low / q_high", "Use quantiles to suggest an initial range for the gate."],
      ["max_points", "Limits the number of points shown in the preview for better performance."],
      ["color_by_dataset", "Colors the scatter plot by dataset when more than one file is loaded."],
      ["Apply gate to images too", "Uses the associated `.pkl` folders to redraw filtered images after gating, in addition to saving gated tables."],
      ["output_dir", "Sets the folder where the gated table and preview outputs will be saved."],
    ],
    outputs: [
      {
        title: "Filtered tables",
        description: "The main output of Gating is a set of CSV files containing only the rows kept by the selected gate.",
        items: [
          "A combined gated CSV table with the rows kept across all selected datasets.",
          "One gated CSV per dataset, so you can continue analysis separately if needed.",
          "A summary table showing how many rows were kept and removed in each dataset.",
        ],
      },
      {
        title: "Preview and logs",
        description: "The module also saves supporting information about the gating step.",
        items: [
          "A preview figure showing the applied rectangular gate.",
          "A log file describing the final gate bounds used in the analysis.",
        ],
      },
      {
        title: "Filtered images from PKL data",
        description: "If you enable image redraw and provide PKL folders, the gate can also be applied to the segmentation image outputs.",
        items: [
          "A new folder of redrawn images showing only the nuclei kept by the gate.",
          "A filtered `pkl-data-filtered` folder for the kept nuclei, which can be useful for later inspection.",
        ],
      },
    ],
    notes: [
      "The goal of gating is to clean the data, not to define phenotypes arbitrarily. Keep thresholds biologically justified.",
      "If you gate multiple datasets together, make sure they use the same column structure.",
    ],
  },
  {
    id: "tutorial-foci",
    title: "Foci Overlay Tutorial",
    intro:
      "Foci Overlay uses `.pkl` results from previous analyses to generate visual overlays and, if needed, profile plots for selected channels.",
    whenToUse: [
      "Use it after segmentation or foci analysis when you want an image-based quality check or a visual output for reporting.",
    ],
    params: [
      ["Pickle (.pkl) folder", "Select the folder that contains the result pickle files generated by the software."],
      ["Saving path", "Sets the output folder for overlay images and tables."],
      ["Channels", "Lists the channels found automatically in the pickle metadata."],
      ["Actions", "Choose whether to create overlays, profile plots, or both."],
      ["Save overlay images", "Controls whether the rendered overlay figures are saved to disk."],
      ["Run Overlay / Stop", "Starts or interrupts the overlay process."],
    ],
    outputs: [
      "Overlay images for the selected channels.",
      "Optional profile plots, depending on the selected action.",
      "Saved tables and visual outputs in the chosen results folder.",
    ],
    notes: [
      "This module depends on previous results, so it is usually used after segmentation-based workflows.",
    ],
  },
  {
    id: "tutorial-nma",
    title: "NMA Tutorial",
    intro:
      "NMA compares cell populations using a selected Area column and a selected irregularity index (NII) column. The workflow combines dataset setup, control-based threshold definition, and final plotting.",
    whenToUse: [
      "Use it when you want to compare morphometric phenotypes across conditions using nuclear or cytoplasm measurements.",
      "When creating new NMA settings, at least one dataset must be marked as Control.",
    ],
    params: [
      ["Add dataset", "Adds a new CSV input row."],
      ["Dataset name", "The label used in the interface and in plots."],
      ["Control", "Marks the reference population used to create NMA settings."],
      ["CSV path", "Path to the dataset file."],
      ["Area column / NII column", "Select the columns used to define the morphometric space. If both nuclear and cytoplasm candidates exist, choose explicitly; if only one compatible column exists, the interface selects it automatically."],
      ["Create NMA settings / Load settings", "Create new thresholds from control data or load an existing configuration."],
      ["Standard Deviations from Area / NII", "Set the ellipse spread around the control population in Step 1."],
      ["Auto (DBSCAN)", "Attempts to detect the core control cluster automatically."],
      ["Step 2 threshold lines", "Manual adjustment stage for the final NII thresholds."],
      ["Dot plot / Heatmap", "Choose the final visualization style."],
      ["Color by / Size by / Hue norm / Size norm", "Define how additional variables are encoded in the final NMA plots."],
      ["Sample size / Palette", "Adjust display performance and appearance for larger datasets."],
      ["Single plot / Overtime / Jointplot", "Change how results are grouped and displayed."],
      ["Saving path / Run NMA / Stop / Save settings", "Control output location, execution, cancellation, and settings export."],
    ],
    outputs: [
      "Saved NMA settings that can be reused later.",
      "Dot plots or heatmaps, depending on the selected visualization mode.",
      "Result images and supporting files written to the chosen output folder.",
      "Execution logs for the NMA run.",
    ],
    notes: [
      "The control population is central to the NMA workflow because it defines the thresholds used later.",
    ],
  },
  {
    id: "tutorial-plot",
    title: "Plot Data Tutorial",
    intro:
      "Plot Data creates exploratory visualizations directly from CSV measurements, including scatter, violin, box, dot, bar, line, rolling average, and CPD-style outputs.",
    whenToUse: [
      "Use it for quick visual inspection of trends, comparisons between conditions, or time-course summaries.",
    ],
    params: [
      ["Datasets", "Load one or more CSV files with the same column structure."],
      ["Graph type", "Choose the type of plot to generate."],
      ["X / Y / Hue / Size", "Map table columns to axes and visual encodings."],
      ["control", "Select a reference condition for workflows that require a control baseline."],
      ["conditionsText / framesText", "Restrict the plot to selected conditions or frames."],
      ["dot / violin_box / violin_points / box_outliers / line_rolling / compute_auc / n", "Additional options that become relevant depending on the selected plot type."],
    ],
    outputs: [
      "The requested plot saved to the output folder.",
      "Additional derived figures when supported by the selected plot type.",
    ],
    notes: [
      "Available columns are inferred from the loaded datasets, so files should follow the same table structure whenever possible.",
    ],
  },
  {
    id: "tutorial-clustering",
    title: "Clustering Tutorial",
    intro:
      "Clustering supports dimensionality reduction and grouping workflows, with a focus on UMAP-style exploration and optional K-means-based coloring.",
    whenToUse: [
      "Use it to inspect multidimensional structure, identify phenotypic neighborhoods, and explore how conditions distribute in feature space.",
    ],
    params: [
      ["Datasets", "Load the CSV files used for embedding and clustering."],
      ["columns", "Select the numeric features used to compute the embedding."],
      ["n_neighbors / min_dist / metric", "Core UMAP parameters that control neighborhood size, compactness, and distance metric."],
      ["method", "Select the embedding approach used in the interface."],
      ["scale", "Standardizes values before dimensionality reduction."],
      ["max_points", "Limits the number of rendered points to keep the preview responsive."],
      ["use_clusters / n_clusters", "Color the embedding by K-means clusters and choose the number of groups."],
      ["k_min / k_max", "Set the range used when generating an elbow plot."],
      ["color_by", "Color the embedding by an existing metadata column instead of clusters."],
    ],
    outputs: [
      "An embedding plot, such as UMAP, based on the selected features.",
      "Optional elbow-plot output to help choose the number of clusters.",
      "Saved result files for later inspection or downstream analysis.",
    ],
    notes: [
      "Clustering is exploratory, so any visible groups should always be interpreted together with biology and metadata.",
    ],
  },
  {
    id: "tutorial-statistics",
    title: "Statistics Tutorial",
    intro:
      "Statistics brings together one-way, two-way, and chi-square analyses for one or more CSV datasets that share the same column structure.",
    whenToUse: [
      "Use one-way analysis for a single grouping factor, two-way analysis for factorial comparisons, and chi-square tests for contingency-style categorical questions.",
    ],
    params: [
      ["Datasets", "Load the CSV inputs that will be combined for statistical testing."],
      ["method", "Choose between one-way, two-way, chi-square, or chi-square subgroup comparison."],
      ["numeric_col", "Select the dependent numeric variable for one-way or two-way analysis."],
      ["group_col / group_col1 / group_col2", "Choose the grouping columns required by the selected test."],
      ["category_col / condition_col", "Select the categorical columns used in chi-square workflows."],
      ["alpha", "Set the significance threshold."],
      ["expected_min", "Define the expected count threshold used in contingency-table decisions."],
      ["correction_method", "Choose the multiple-testing correction strategy."],
      ["pairs_text", "List any pairwise comparisons you want to prioritize."],
      ["filters", "Apply extra column-based filters before running the analysis."],
    ],
    outputs: [
      "Statistical result tables saved to the output folder.",
      "Logs summarizing the selected test and the analysis flow.",
      "Post-hoc or contingency-table outputs when supported by the selected method.",
    ],
    notes: [
      "This module works best with clean input tables and clearly defined grouping columns.",
      "Statistical outputs support exploration, but they should still be interpreted in the context of the study design.",
    ],
  },
  {
    id: "tutorial-tracking",
    title: "Tracking Tutorial",
    intro:
      "Tracking reconstructs cell trajectories over time and supports manual correction after automatic linking.",
    whenToUse: [
      "Use it when you need trajectory-level information across frames, including migration paths and lineage events.",
    ],
    params: [
      ["path_to_table", "Select the measurement table used as tracking input."],
      ["image_dir", "Select the folder containing the corresponding images."],
      ["image_col", "Choose the column that identifies the image name or frame source."],
      ["max_distance", "Set the maximum allowed displacement between linked objects."],
      ["time_window", "Set the temporal window used for association."],
      ["max_split_distance", "Set the maximum distance allowed when assigning division events."],
      ["max_gap_closing_distance", "Set the tolerance for reconnecting interrupted tracks."],
      ["frame / max_frame / trail_window", "Viewer controls for navigating the time series and adjusting the trail display."],
      ["show_complete_trail", "Shows the full trajectory instead of only the recent trail."],
      ["save_results_dir", "Sets the output folder for corrected tracking results."],
    ],
    outputs: [
      "Tracking result tables with linked trajectories.",
      "Corrected outputs after manual editing, when applicable.",
      "Saved tracking files in the selected results folder.",
    ],
    notes: [
      "Manual correction is part of the workflow, so linking, unlinking, and marking cell divisions are expected editing steps.",
    ],
  },
];
const HOME_RESOURCES = [
  "Use the accompanying article or thesis for the full scientific rationale behind each analysis module.",
  "Use the Home page as a quick guide before moving into the working tabs.",
  "If a run fails, save the logs shown in the interface before reporting the issue.",
  "Whenever possible, keep raw data and processed outputs in separate folders to make reruns safer.",
];
const MODULE_TUTORIAL_SECTION = {
  "Image Registration": "tutorial-registration",
  Segmentation: "tutorial-segmentation",
  Gating: "tutorial-gating",
  "Foci Overlay": "tutorial-foci",
  NMA: "tutorial-nma",
  "Plot Data": "tutorial-plot",
  Clustering: "tutorial-clustering",
  Statistics: "tutorial-statistics",
  Tracking: "tutorial-tracking",
};
const PALETTE_OPTIONS = ["viridis", "plasma", "magma", "inferno", "cividis", "coolwarm", "Spectral", "RdBu"];
const sameArray = (a = [], b = []) => a.length === b.length && a.every((v, i) => v === b[i]);
const makeStatsFilterRow = () => ({ id: makeRowId(), column: "", values: [] });
const normalizeFilterOption = (value) => String(value ?? "").trim();
const copyText = async (text) => {
  const normalized = String(text ?? "");
  if (!normalized) return false;
  try {
    await navigator.clipboard.writeText(normalized);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = normalized;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return !!ok;
  }
};
const scrollToTopSmooth = () => {
  if (typeof window === "undefined") return;
  window.scrollTo({ top: 0, behavior: "smooth" });
};
const STORAGE_KEYS = {
  activeModule: "fornma.activeModule",
  plotJob: "fornma.plotJob",
  segJob: "fornma.segJob",
  regJob: "fornma.regJob",
  fociJob: "fornma.fociJob",
};
const DEFAULT_PLOT_JOB = {
  job_id: null,
  status: "idle",
  progress: 0,
  message: "",
  files: [],
  output_dir: "",
  error: "",
};
const DEFAULT_SEG_JOB = {
  job_id: null,
  status: "idle",
  progress: 0,
  message: "",
  log: "",
  preview_path: "",
  preview_paths: [],
  preview_index: null,
  error: "",
};
const DEFAULT_REG_JOB = {
  job_id: null,
  status: "idle",
  progress: 0,
  done: 0,
  total: 0,
  message: "",
  log: "",
  error: "",
};
const DEFAULT_FOCI_JOB = {
  job_id: null,
  status: "idle",
  progress: 0,
  message: "",
  log: "",
  error: "",
};
const PLOT_TYPES_REQUIRE_XY = new Set(["scatter"]);
const PLOT_TYPES_REQUIRE_Y = new Set(["scatter", "violin", "box", "dot", "bar", "line", "rolling-average"]);
const PLOT_TYPES_SUPPORT_DOT = new Set(["box"]);
const PLOT_TYPES_SUPPORT_SIZE = new Set(["scatter", "dot"]);
const PLOT_TYPES_SUPPORT_X = new Set(["scatter", "violin", "box", "dot", "bar", "line"]);
const initialPlotConfig = () => ({
  kind: "dot",
  dot: {
    column1: "",
    column2: "",
    hue_min: "",
    hue_max: "",
    size_min: "",
    size_max: "",
    sample_size: "",
    palette: "",
    single: false,
    overtime: false,
  },
  heatmap: {
    single: false,
    overtime: false,
    jointplot: false,
    palette: "",
  },
});
const initialPlotDataState = () => ({
  datasets: [{ id: makeRowId(), name: "Dataset 1", path: "", columns: null, enabled: true }],
  graph_type: "scatter",
  x: "",
  y: "",
  hue: "",
  size: "",
  violin_box: true,
  violin_points: true,
  box_outliers: false,
  line_rolling: false,
  compute_auc: false,
  control: "",
  controlOptions: [],
  conditionsText: "",
  framesText: "",
  dot: false,
  n: "",
  columns: [],
  categoricalColumns: [],
  columnsWarning: "",
  figure: null,
  message: "",
});
const initialClusteringState = () => ({
  datasets: [{ id: makeRowId(), name: "Dataset 1", path: "", enabled: true }],
  columnsAll: [],
  numericColumns: [],
  columns: [],
  n_neighbors: 15,
  min_dist: 0.1,
  metric: "euclidean",
  method: "umap",
  scale: true,
  max_points: 12000,
  use_clusters: false,
  n_clusters: 8,
  k_min: 2,
  k_max: 12,
  color_by: "",
  figure: null,
  elbowFigure: null,
  message: "",
});
const initialStatsState = () => ({
  datasets: [{ id: makeRowId(), name: "Dataset 1", path: "", enabled: true }],
  method: "oneway",
  columns: [],
  categoricalColumns: [],
  numeric_col: "",
  group_col: "",
  group_col1: "",
  group_col2: "",
  category_col: "",
  condition_col: "",
  alpha: 0.05,
  expected_min: 5.0,
  correction_method: "auto",
  pairs_text: "",
  filters: [makeStatsFilterRow()],
  filterValueOptions: {},
  tables: [],
  log: "",
  message: "",
});
const initialGatingState = () => ({
  datasets: [{ id: makeRowId(), name: "Dataset 1", path: "", pkl_dir: "", enabled: true }],
  columns: [],
  numericColumns: [],
  x_col: "",
  y_col: "",
  x_min: "",
  x_max: "",
  y_min: "",
  y_max: "",
  q_low: 0.05,
  q_high: 0.95,
  max_points: 12000,
  color_by_dataset: true,
  draw_images: false,
  output_dir: "",
  figure: null,
  tables: [],
  files: [],
  message: "",
});
const initialTrackingState = () => ({
  path_to_table: "",
  image_dir: "",
  image_col: "",
  columns: [],
  preview_cache_dir: "",
  preview_image_path: "",
  preview_nonce: 0,
  viewer_w: 0,
  viewer_h: 0,
  max_distance: 30,
  time_window: 5,
  max_split_distance: 10,
  max_gap_closing_distance: 30,
  table_path: "",
  frame: 0,
  max_frame: 0,
  trail_window: 7,
  show_complete_trail: false,
  figure: null,
  selected: [],
  selected_markers: [],
  undo_checkpoint_path: "",
  saved_progress_path: "",
  finish_open: false,
  message: "",
  total_rows: 0,
  total_tracks: 0,
  workflow_stage: "step1",
  save_results_dir: "",
});

function readStorage(key, fallback) {
  if (typeof window === "undefined") return fallback;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

function FolderIcon() {
  return (
    <svg className="btn-icon" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3.5 6.5h6.2l1.8 2h9v9.8a2.2 2.2 0 0 1-2.2 2.2H5.7a2.2 2.2 0 0 1-2.2-2.2Z" />
      <path d="M3.5 8.5h17" />
    </svg>
  );
}

function BrowseLabel({ children = "Browse" }) {
  return (
    <span className="browse-label">
      <FolderIcon />
      <span className="sr-only">{children}</span>
    </span>
  );
}

function DatasetBadge({ children }) {
  return <span className="dataset-badge">{children}</span>;
}

function DatasetCollapseButton({ collapsed, onClick, label = "dataset" }) {
  return (
    <button
      type="button"
      className="collapse-toggle"
      aria-label={`${collapsed ? "Expand" : "Collapse"} ${label}`}
      aria-expanded={!collapsed}
      onClick={onClick}
    >
      <span className={`collapse-caret ${collapsed ? "collapsed" : "expanded"}`} aria-hidden="true" />
    </button>
  );
}

function hasFilledFields(item = {}) {
  return Object.entries(item).some(([key, value]) => {
    if (["id", "enabled", "is_control", "columns", "area_columns", "nii_columns"].includes(key)) return false;
    if (Array.isArray(value)) return value.length > 0;
    if (value && typeof value === "object") return Object.keys(value).length > 0;
    return String(value ?? "").trim() !== "";
  });
}

function confirmRemoveFilled(item, label = "this item") {
  if (!hasFilledFields(item)) return true;
  return window.confirm(`Remove ${label}? This item already has filled fields, and this action cannot be undone.`);
}

function EmptyState({ title, text }) {
  return (
    <div className="empty-state">
      <div className="empty-state-icon" aria-hidden="true">+</div>
      <div>
        <h3>{title}</h3>
        <p>{text}</p>
      </div>
    </div>
  );
}

function Tip({ text }) {
  const [open, setOpen] = React.useState(false);
  const [position, setPosition] = React.useState({ left: 0, top: 0 });
  const buttonRef = React.useRef(null);
  const closeTimerRef = React.useRef(null);

  React.useEffect(() => () => {
    if (closeTimerRef.current) window.clearTimeout(closeTimerRef.current);
  }, []);

  const toggleTip = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (closeTimerRef.current) {
      window.clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
    const rect = buttonRef.current?.getBoundingClientRect();
    if (rect && typeof window !== "undefined") {
      setPosition({
        left: Math.min(window.innerWidth - 150, Math.max(150, rect.left + rect.width / 2)),
        top: Math.max(12, rect.top - 10),
      });
    }
    setOpen((v) => !v);
  };

  return (
    <span className="tip-wrap">
      <button
        ref={buttonRef}
        type="button"
        className="tip-badge"
        aria-label={text}
        aria-expanded={open}
        onClick={toggleTip}
        onBlur={() => {
          closeTimerRef.current = window.setTimeout(() => setOpen(false), 160);
        }}
      >
        i
      </button>
      {open && typeof document !== "undefined" && createPortal(
        <span
          className="tip-popover"
          role="tooltip"
          style={{ left: position.left, top: position.top }}
          onMouseDown={(event) => event.preventDefault()}
        >
          {text}
        </span>,
        document.body
      )}
    </span>
  );
}

function HomeLeftPanel({ activeSection, onSelectSection }) {
  return (
    <Card as="aside" className="panel seg-panel home-panel" variant="panel">
      <div className="seg-header">
        <h3>Get Started</h3>
        <p className="hint">Use this sidebar as an index for the software overview, tutorials, and useful links.</p>
      </div>
      <div className="seg-scroll">
        <div className="home-index">
          {HOME_SECTIONS.map((section) => (
            <button
              key={section.id}
              type="button"
              className={`home-index-item ${activeSection === section.id ? "active" : ""}`}
              onClick={() => onSelectSection(section.id)}
            >
              {section.title}
            </button>
          ))}
        </div>
      </div>
    </Card>
  );
}

function HomeTutorialSection({ title, intro, whenToUse = [], params = [], paramGroups = [], outputs = [], notes = [] }) {
  return (
    <>
      <h3>{title}</h3>
      <p className="hint hint-muted">{intro}</p>
      {whenToUse.length > 0 && (
        <details className="home-detail-block home-copy-block" open>
          <summary>
            <span>When to use</span>
            <span className="home-detail-hint">Click to expand or collapse</span>
          </summary>
          <ul className="home-bullet-list">
            {whenToUse.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
      )}
      {(params.length > 0 || paramGroups.length > 0) && (
        <details className="home-detail-block home-copy-block">
          <summary>
            <span>Key interface parameters</span>
            <span className="home-detail-hint">Click to expand or collapse</span>
          </summary>
          {paramGroups.length > 0 ? (
            <div className="home-param-groups">
              {paramGroups.map((group) => (
                <div key={group.title} className="home-param-group">
                  <h4>{group.title}</h4>
                  <ul className="home-param-list">
                    {group.items.map(([label, text]) => (
                      <li key={`${group.title}-${label}`} className="home-param-item">
                        <strong>{label}:</strong> {text}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : (
            <ul className="home-param-list">
              {params.map(([label, text]) => (
                <li key={label} className="home-param-item">
                  <strong>{label}:</strong> {text}
                </li>
              ))}
            </ul>
          )}
        </details>
      )}
      {(title === "Image Registration Tutorial" || title === "Segmentation Tutorial") && (
        <details className="home-detail-block home-copy-block" open>
          <summary>
            <span>How to use Load images</span>
            <span className="home-detail-hint">Click to expand or collapse</span>
          </summary>
          <p className="hint hint-muted">
            The <strong>Load images</strong> window is often the least intuitive part of the interface for new users,
            so it helps to think of it as a map of your experiment. The table does not ask for single image files. It
            asks for folders that contain the image sequence for each condition and each channel.
          </p>
          <ol className="home-number-list">
            {HOME_LOAD_IMAGES_GUIDE.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ol>
          <p className="hint hint-muted">
            Before saving, check whether the table matches the way you would describe the experiment out loud. For
            example: “Control, DAPI folder” should point to the DAPI images for the control condition, and “Treatment,
            GFP folder” should point to the GFP images for the treatment condition.
          </p>
        </details>
      )}
      {outputs.length > 0 && (
        <details className="home-detail-block home-copy-block" open>
          <summary>
            <span>Outputs</span>
            <span className="home-detail-hint">Click to expand or collapse</span>
          </summary>
          {outputs.every((item) => typeof item === "object" && item !== null && Array.isArray(item.items)) ? (
            <div className="home-output-groups">
              {outputs.map((group) => (
                <div key={group.title} className="home-output-group">
                  <h4>{group.title}</h4>
                  {group.description ? <p className="hint hint-muted">{group.description}</p> : null}
                  <ul className="home-bullet-list">
                    {group.items.map((item) => (
                      <li key={`${group.title}-${item}`}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          ) : (
            <ul className="home-bullet-list">
              {outputs.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          )}
        </details>
      )}
      {notes.length > 0 && (
        <details className="home-detail-block home-copy-block">
          <summary>
            <span>Notes</span>
            <span className="home-detail-hint">Click to expand or collapse</span>
          </summary>
          <ul className="home-bullet-list">
            {notes.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
      )}
    </>
  );
}

function previewMeta(path) {
  const parts = String(path || "").split("/").filter(Boolean);
  const channel = parts.length >= 2 ? parts[parts.length - 2] : "";
  const condition = parts.length >= 3 ? parts[parts.length - 3] : "";
  return { channel, condition };
}

function defaultChannelName(index) {
  return `Channel ${index + 1}`;
}

function channelNameOrDefault(channel, index) {
  return String(channel?.name || "").trim() || defaultChannelName(index);
}

function SegmentationLeftPanel({ onPickDirectory, onStartSegmentation, onStopSegmentation, onResetSegmentation, segJob }) {
  const resetSegForm = () => {
    const ok = window.confirm("Reset all segmentation settings to defaults?");
    if (!ok) return;
    onResetSegmentation?.();
  };

  const [savePath, setSavePath] = useState("");
  const [imagesData, setImagesData] = useState({
    channels: [{ id: "ch1", name: "Channel 1" }],
    rows: [{ condition: "Control", ch1: "" }],
  });
  const [modalOpen, setModalOpen] = useState(false);
  const [modalError, setModalError] = useState("");
  const [summaryText, setSummaryText] = useState("No images loaded yet.");
  const [nuclearChannel, setNuclearChannel] = useState("ch1");
  const [fociEnabled, setFociEnabled] = useState(false);
  const [fociChannels, setFociChannels] = useState([]);
  const [cytoEnabled, setCytoEnabled] = useState(false);
  const [cytoChannels, setCytoChannels] = useState([]);
  const [segmentationTarget, setSegmentationTarget] = useState("nucleus");
  const [cytoplasmChannel, setCytoplasmChannel] = useState("ch1");
  const [segMethod, setSegMethod] = useState("fornma");
  const [overtime, setOvertime] = useState(false);
  const [magnification, setMagnification] = useState(20);
  const [pixelSize, setPixelSize] = useState(0.6);
  const [rescaleIntensity, setRescaleIntensity] = useState(false);
  const [removeBackground, setRemoveBackground] = useState(false);
  const [rollingRadius, setRollingRadius] = useState(50);
  const [fornmaThreshold, setFornmaThreshold] = useState("triangle");
  const [fornmaOffset, setFornmaOffset] = useState(5);
  const [fornmaSmooth, setFornmaSmooth] = useState(12);
  const [fornmaAdjustSize, setFornmaAdjustSize] = useState(0);
  const [fornmaCutEdges, setFornmaCutEdges] = useState(0.7);
  const [fornmaFindLow, setFornmaFindLow] = useState(false);
  const [fornmaWeakly, setFornmaWeakly] = useState(false);
  const [cellposeModel, setCellposeModel] = useState("nuclei");
  const [cellposeDiameter, setCellposeDiameter] = useState(25);
  const [cellposeFlow, setCellposeFlow] = useState(0.4);
  const [cellposeCellprob, setCellposeCellprob] = useState(-3);
  const [cellposeUseGpu, setCellposeUseGpu] = useState(true);
  const [cellposeInvert, setCellposeInvert] = useState(true);
  const [cytoCellposeModel, setCytoCellposeModel] = useState("cyto3");
  const [cytoCellposeDiameter, setCytoCellposeDiameter] = useState(25);
  const [cytoCellposeFlow, setCytoCellposeFlow] = useState(0.4);
  const [cytoCellposeCellprob, setCytoCellposeCellprob] = useState(-3);
  const [cytoCellposeInvert, setCytoCellposeInvert] = useState(true);
  const [cytoRescaleIntensity, setCytoRescaleIntensity] = useState(false);
  const [cytoRemoveBackground, setCytoRemoveBackground] = useState(false);
  const [cytoRollingRadius, setCytoRollingRadius] = useState(50);
  const [advEnable, setAdvEnable] = useState({
    shape: true,
    eccentricity: false,
    min_size: false,
    max_size: false,
    min_radius: false,
    max_radius: false,
  });
  const [advValues, setAdvValues] = useState({
    shape: 0.88,
    eccentricity: 0.8,
    min_size: 100,
    max_size: 10000,
    min_radius: 4,
    max_radius: 120,
  });
  const [cytoAdvEnable, setCytoAdvEnable] = useState({
    shape: false,
    eccentricity: false,
    min_size: false,
    max_size: false,
    min_radius: false,
    max_radius: false,
  });
  const [cytoAdvValues, setCytoAdvValues] = useState({
    shape: 0.88,
    eccentricity: 0.8,
    min_size: 100,
    max_size: 10000,
    min_radius: 4,
    max_radius: 120,
  });
  const [channelCfg, setChannelCfg] = useState({});
  const channels = imagesData.channels || [];
  const channelIds = new Set(channels.map((c) => c.id));

  useEffect(() => {
    if (channels.length === 0) return;
    if (!channelIds.has(nuclearChannel)) {
      setNuclearChannel(channels[0].id);
    }
    if (!channelIds.has(cytoplasmChannel)) {
      setCytoplasmChannel(channels[0].id);
    }
    setFociChannels((prev) => prev.filter((id) => channelIds.has(id)));
    setCytoChannels((prev) => prev.filter((id) => channelIds.has(id)));
  }, [imagesData.channels]);

  useEffect(() => {
    setChannelCfg((prev) => {
      const next = { ...prev };
      channels.forEach((ch) => {
        if (next[ch.id]) return;
        next[ch.id] = {
          rescale_intensity: true,
          remove_background: true,
          rolling_ball_radius: 40,
          match_histograms: false,
          ring_size: 3,
          use_ellipse: true,
          foci_min_size: 7,
          foci_max_size_enable: false,
          foci_max_size: 20,
          foci_min_int_enable: false,
          foci_min_int: 0,
          foci_max_int_enable: false,
          foci_max_int: 1,
          foci_prominence: 1.2,
          measure_nucleus: true,
          measure_cytoplasm: false,
        };
      });
      Object.keys(next).forEach((k) => {
        if (!channelIds.has(k)) delete next[k];
      });
      return next;
    });
  }, [imagesData.channels]);

  const setAdvToggle = (key, value) => setAdvEnable((prev) => ({ ...prev, [key]: value }));
  const setAdvValue = (key, value) => setAdvValues((prev) => ({ ...prev, [key]: value }));
  const setCytoAdvToggle = (key, value) => setCytoAdvEnable((prev) => ({ ...prev, [key]: value }));
  const setCytoAdvValue = (key, value) => setCytoAdvValues((prev) => ({ ...prev, [key]: value }));
  const setChCfg = (chId, patch) => {
    setChannelCfg((prev) => ({ ...prev, [chId]: { ...(prev[chId] || {}), ...patch } }));
  };

  const addCondition = () => {
    setImagesData((prev) => {
      const row = { condition: "" };
      (prev.channels || []).forEach((ch) => { row[ch.id] = ""; });
      return { ...prev, rows: [...(prev.rows || []), row] };
    });
  };

  const addChannel = () => {
    setImagesData((prev) => {
      const maxIdx = Math.max(0, ...(prev.channels || []).map((ch) => Number((ch.id || "").replace("ch", "")) || 0));
      const newId = `ch${maxIdx + 1}`;
      const nextChannels = [...(prev.channels || []), { id: newId, name: `Channel ${maxIdx + 1}` }];
      const nextRows = (prev.rows || []).map((r) => ({ ...r, [newId]: "" }));
      return { ...prev, channels: nextChannels, rows: nextRows };
    });
  };

  const removeCondition = (rowIdx) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).filter((_, i) => i !== rowIdx),
    }));
  };

  const removeChannel = (chId) => {
    setImagesData((prev) => {
      const nextChannels = (prev.channels || []).filter((ch) => ch.id !== chId);
      const nextRows = (prev.rows || []).map((r) => {
        const copy = { ...r };
        delete copy[chId];
        return copy;
      });
      return { ...prev, channels: nextChannels, rows: nextRows };
    });
    setFociChannels((prev) => prev.filter((id) => id !== chId));
    setCytoChannels((prev) => prev.filter((id) => id !== chId));
  };

  const updateChannelName = (chId, name) => {
    setImagesData((prev) => ({
      ...prev,
      channels: (prev.channels || []).map((ch) => (ch.id === chId ? { ...ch, name } : ch)),
    }));
  };

  const updateCondition = (rowIdx, condition) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).map((r, i) => (i === rowIdx ? { ...r, condition } : r)),
    }));
  };

  const updatePathCell = (rowIdx, chId, path) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).map((r, i) => (i === rowIdx ? { ...r, [chId]: path } : r)),
    }));
  };

  const browsePathCell = async (rowIdx, chId) => {
    const picked = await onPickDirectory();
    if (!picked) return;
    updatePathCell(rowIdx, chId, picked);
  };

  const saveImagesTable = () => {
    const errors = [];
    const chs = imagesData.channels || [];
    const rows = imagesData.rows || [];

    const normalizedChannels = chs.map((ch, idx) => ({ ...ch, name: channelNameOrDefault(ch, idx) }));
    const chNames = normalizedChannels.map((c) => c.name);
    if (new Set(chNames).size !== chNames.length) errors.push("Each channel needs a unique name. Rename duplicate channel columns before saving.");

    const conds = rows.map((r) => (r.condition || "").trim());
    if (conds.some((c) => !c)) errors.push("Each row needs a condition name, for example Control or Treatment.");
    if (new Set(conds).size !== conds.length) errors.push("Each condition name must be unique. Rename duplicate rows before saving.");

    rows.forEach((r, idx) => {
      normalizedChannels.forEach((ch) => {
        const p = (r[ch.id] || "").trim();
        if (!p) errors.push(`Row ${idx + 1}, ${ch.name}: choose the image folder for this condition/channel cell.`);
      });
    });

    if (errors.length) {
      setModalError(errors.join("\n"));
      return;
    }

    const lines = [`Image selection OK:`, `Conditions: ${rows.length} | Channels: ${chs.length}`, ""];
    rows.forEach((r) => {
      lines.push(`- ${r.condition}:`);
      normalizedChannels.forEach((ch) => lines.push(`    ${ch.name}: ${r[ch.id] || ""}`));
    });
    setImagesData((prev) => ({ ...prev, channels: normalizedChannels }));
    setSummaryText(lines.join("\n"));
    setModalError("");
    setModalOpen(false);
  };

  const counterText = `Channels: ${channels.length} | Conditions: ${(imagesData.rows || []).length}`;

  const buildSegDataPayload = () => {
    const channelsMap = {};
    channels.forEach((ch, idx) => {
      const cfg = channelCfg[ch.id] || {};
      channelsMap[ch.id] = {
        name: channelNameOrDefault(ch, idx),
        rescale_intensity: !!cfg.rescale_intensity,
        remove_background: !!cfg.remove_background,
        rolling_ball_radius: Number(cfg.rolling_ball_radius ?? 40),
        match_histograms: !!cfg.match_histograms,
        measure_nucleus: segmentationTarget !== "cytoplasm" && !!cfg.measure_nucleus,
        measure_cytoplasm: segmentationTarget === "cytoplasm" ? true : (segmentationTarget === "both" && !!cfg.measure_cytoplasm),
        wants_ktr: cytoEnabled && cytoChannels.includes(ch.id),
        ring_size: showNumber(cfg.ring_size, 3),
        use_ellipse: !!cfg.use_ellipse,
        wants_foci: fociEnabled && fociChannels.includes(ch.id),
        foci_min_size: showNumber(cfg.foci_min_size, 7),
        foci_max_size: cfg.foci_max_size_enable ? showNumber(cfg.foci_max_size, 20) : false,
        foci_min_int: cfg.foci_min_int_enable ? showNumber(cfg.foci_min_int, 0) : false,
        foci_max_int: cfg.foci_max_int_enable ? showNumber(cfg.foci_max_int, 1) : false,
        foci_prominence: showNumber(cfg.foci_prominence, 1.2),
      };
    });

    return {
      general: {
        path_to_save: savePath,
        segmentation_mode: segmentationTarget,
        channel_with_nuclei: nuclearChannel || null,
        channel_with_cytoplasm: cytoplasmChannel || null,
        overtime: !!overtime,
      },
      segmentation: {
        magnification: showNumber(magnification, 20),
        "pixel-size": showNumber(pixelSize, 0.6),
        "rescale-intensity": !!rescaleIntensity,
        "remove-bg": !!removeBackground,
        "rolling-radius": showNumber(rollingRadius, 50),
        seg_method: segMethod,
      },
      fornma: {
        threshold: fornmaThreshold,
        offset: showNumber(fornmaOffset, 5),
        smooth: showNumber(fornmaSmooth, 12),
        adjust_size: showNumber(fornmaAdjustSize, 0),
        cut_edges: showNumber(fornmaCutEdges, 0.7),
        find_low_intensity_nucleus: !!fornmaFindLow,
        weakly_labeled: !!fornmaWeakly,
      },
      cellpose: {
        model_type: cellposeModel || "nuclei",
        diameter: showNumber(cellposeDiameter, 25),
        flow_threshold: showNumber(cellposeFlow, 0.4),
        cellprob_threshold: showNumber(cellposeCellprob, -3),
        use_gpu: !!cellposeUseGpu,
        invert: !!cellposeInvert,
      },
      cytoplasm_cellpose: {
        model_type: cytoCellposeModel || "cyto3",
        diameter: showNumber(cytoCellposeDiameter, 25),
        flow_threshold: showNumber(cytoCellposeFlow, 0.4),
        cellprob_threshold: showNumber(cytoCellposeCellprob, -3),
        invert: !!cytoCellposeInvert,
        rescale_intensity: !!cytoRescaleIntensity,
        remove_bg: !!cytoRemoveBackground,
        radius_bg: showNumber(cytoRollingRadius, 50),
      },
      filters: {
        shape: advEnable.shape ? showNumber(advValues.shape, 0.88) : null,
        eccentricity: advEnable.eccentricity ? showNumber(advValues.eccentricity, 0.8) : null,
        minimum_size: advEnable.min_size ? showNumber(advValues.min_size, 100) : null,
        maximum_size: advEnable.max_size ? showNumber(advValues.max_size, 10000) : null,
        minimum_radius: advEnable.min_radius ? showNumber(advValues.min_radius, 4) : null,
        maximum_radius: advEnable.max_radius ? showNumber(advValues.max_radius, 120) : null,
      },
      cytoplasm_filters: {
        shape: cytoAdvEnable.shape ? showNumber(cytoAdvValues.shape, 0.88) : null,
        eccentricity: cytoAdvEnable.eccentricity ? showNumber(cytoAdvValues.eccentricity, 0.8) : null,
        minimum_size: cytoAdvEnable.min_size ? showNumber(cytoAdvValues.min_size, 100) : null,
        maximum_size: cytoAdvEnable.max_size ? showNumber(cytoAdvValues.max_size, 10000) : null,
        minimum_radius: cytoAdvEnable.min_radius ? showNumber(cytoAdvValues.min_radius, 4) : null,
        maximum_radius: cytoAdvEnable.max_radius ? showNumber(cytoAdvValues.max_radius, 120) : null,
      },
      channels: channelsMap,
    };
  };

  const showNumber = (v, fallback) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : fallback;
  };

  const startSeg = async (preview) => {
    const payload = {
      images_data: imagesData,
      seg_data: buildSegDataPayload(),
      preview: !!preview,
      preview_index: preview ? 0 : null,
    };
    await onStartSegmentation(payload);
  };

  const segRunning =
    segJob?.status === "starting" ||
    segJob?.status === "running" ||
    segJob?.status === "queued" ||
    segJob?.status === "canceling";
  const segCanceling = segJob?.status === "canceling";
  const segCanceled = segJob?.status === "canceled";

  return (
    <>
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Segmentation Settings</h3>
        <p className="hint">Configure image inputs, nucleus detection, and per-channel measurement options.</p>
      </div>

      <div className="seg-scroll">
        <div className="sidebar-control-block">
        <div className="row">
          <button className="secondary" onClick={() => { setModalError(""); setModalOpen(true); }}>Load images</button>
          <button className="ghost" onClick={resetSegForm} disabled={segRunning}>Reset settings</button>
        </div>
        <div className="field-head">Saving path <Tip text="Where outputs (tables, images, logs) will be written." /></div>
        <div className="row path-row">
          <input
            className="input"
            value={savePath}
            onChange={(e) => setSavePath(e.target.value)}
            placeholder="Folder to save results..."
          />
          <button
            className="secondary"
            onClick={async () => {
              const p = await onPickDirectory();
              if (p) setSavePath(p);
            }}
          >
            <BrowseLabel>Browse</BrowseLabel>
          </button>
        </div>
        <details className="seg-summary">
          <summary>Image selection summary</summary>
          <pre>{summaryText}</pre>
        </details>
        </div>
        <details open className="seg-section">
          <summary>General Settings</summary>
          <div className="seg-body">
            <div className="field-head">Segmentation Target <Tip text="Choose whether to segment nuclei, cytoplasm, or both compartments." /></div>
            <div className="row">
              <label className="radio"><input type="radio" checked={segmentationTarget === "nucleus"} onChange={() => setSegmentationTarget("nucleus")} /> Nucleus</label>
              <label className="radio"><input type="radio" checked={segmentationTarget === "cytoplasm"} onChange={() => setSegmentationTarget("cytoplasm")} /> Cytoplasm</label>
              <label className="radio"><input type="radio" checked={segmentationTarget === "both"} onChange={() => setSegmentationTarget("both")} /> Both</label>
            </div>
            {segmentationTarget !== "cytoplasm" && (
              <>
                <div className="field-head">Nuclear Detection <Tip text="Pick the channel that contains nuclei for detection." /></div>
                <select className="input" value={nuclearChannel} onChange={(e) => setNuclearChannel(e.target.value)}>
                  <option value="">Select one channel...</option>
                  {channels.map((ch) => <option key={ch.id} value={ch.id}>{ch.name}</option>)}
                </select>
              </>
            )}
            {segmentationTarget !== "nucleus" && (
              <>
                <div className="field-head">Cytoplasm Detection <Tip text="Pick the channel used to generate cytoplasm masks with Cellpose. For cells imaged in visible light or brightfield, start with model cyto3, Flow Threshold 0.6-0.8, and Cellprob Threshold -3 or -4." /></div>
                <select className="input" value={cytoplasmChannel} onChange={(e) => setCytoplasmChannel(e.target.value)}>
                  <option value="">Select one channel...</option>
                  {channels.map((ch) => <option key={ch.id} value={ch.id}>{ch.name}</option>)}
                </select>
              </>
            )}
            <label className="checkbox">
              <input type="checkbox" checked={overtime} onChange={(e) => setOvertime(e.target.checked)} />
              Overtime <Tip text="Check this if images represent time sequence." />
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={fociEnabled} onChange={(e) => setFociEnabled(e.target.checked)} />
              Foci <Tip text="Enable spot (foci) detection and extra foci parameters for selected channels." />
            </label>
            {fociEnabled && (
              <>
                <div className="field-head">Channels for Foci</div>
                <div className="multi-picker">
                  {channels.map((ch) => (
                    <label className="checkbox" key={`f-${ch.id}`}>
                      <input
                        type="checkbox"
                        checked={fociChannels.includes(ch.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFociChannels((prev) => Array.from(new Set([...prev, ch.id])));
                          } else {
                            setFociChannels((prev) => prev.filter((id) => id !== ch.id));
                          }
                        }}
                      />
                      {ch.name}
                    </label>
                  ))}
                </div>
                <p className="hint">You can select multiple channels.</p>
              </>
            )}
            <label className="checkbox">
              <input type="checkbox" checked={cytoEnabled} onChange={(e) => setCytoEnabled(e.target.checked)} />
              Cytoplasmatic Ring <Tip text="Enable translocation (cytoplasmatic ring) parameters for selected channels." />
            </label>
            {cytoEnabled && (
              <>
                <div className="field-head">Channels for Cytoplasmatic Ring</div>
                <div className="multi-picker">
                  {channels.map((ch) => (
                    <label className="checkbox" key={`c-${ch.id}`}>
                      <input
                        type="checkbox"
                        checked={cytoChannels.includes(ch.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setCytoChannels((prev) => Array.from(new Set([...prev, ch.id])));
                          } else {
                            setCytoChannels((prev) => prev.filter((id) => id !== ch.id));
                          }
                        }}
                      />
                      {ch.name}
                    </label>
                  ))}
                </div>
                <p className="hint">You can select multiple channels.</p>
              </>
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Segmentation Settings</summary>
          <div className="seg-body">
            <div className="row">
              <div className="metric">
                <label>Magnification <Tip text="Numeric objective magnification used for acquisition (e.g. 20x)." /></label>
                <input type="number" className="input" value={magnification} onChange={(e) => setMagnification(e.target.value)} />
              </div>
            </div>
            <div className="row">
              <div className="metric">
                <label>Pixel Size <Tip text="Real sample distance represented by each pixel." /></label>
                <input type="number" className="input" value={pixelSize} onChange={(e) => setPixelSize(e.target.value)} step="0.1" />
              </div>
            </div>
            {segmentationTarget !== "cytoplasm" && (
              <details open className="seg-compartment seg-compartment-nuc">
                <summary>Nuclear Segmentation</summary>
                <div className="seg-compartment-body">
                <label className="checkbox">
                  <input type="checkbox" checked={rescaleIntensity} onChange={(e) => setRescaleIntensity(e.target.checked)} />
                  Rescale Intensity <Tip text="Normalize intensity values before nuclear segmentation." />
                </label>
                <label className="checkbox">
                  <input type="checkbox" checked={removeBackground} onChange={(e) => setRemoveBackground(e.target.checked)} />
                  Remove Background <Tip text="Subtract smooth background before nuclear segmentation." />
                </label>
                {removeBackground && (
                  <>
                    <div className="field-head">Rolling Radius (px) <Tip text="Radius used for background removal before nuclear segmentation." /></div>
                    <input className="input" type="number" value={rollingRadius} onChange={(e) => setRollingRadius(e.target.value)} />
                  </>
                )}
                <div className="field-head">Segmentation Method <Tip text="Choose forNMA (faster) or Cellpose (more robust) pipeline." /></div>
                <div className="row">
                  <label className="radio"><input type="radio" checked={segMethod === "fornma"} onChange={() => setSegMethod("fornma")} /> forNMA</label>
                  <label className="radio"><input type="radio" checked={segMethod === "cellpose"} onChange={() => setSegMethod("cellpose")} /> Cellpose</label>
                </div>
                {segMethod === "fornma" ? (
                  <>
                    <h4 className="seg-subtitle">forNMA Parameters</h4>
                    <div className="field-head">Threshold <Tip text="Threshold strategy used to separate nuclei from background." /></div>
                    <div className="seg-threshold-wrap">
                    <select className="input seg-threshold-input" value={fornmaThreshold} onChange={(e) => setFornmaThreshold(e.target.value)}>
                      <option value="isodata">Isodata</option>
                      <option value="li">Li</option>
                      <option value="mean">Mean</option>
                      <option value="minimum">Minimum</option>
                      <option value="median">Median</option>
                      <option value="multi_otsu">Multi-Otsu</option>
                      <option value="otsu">Otsu</option>
                      <option value="triangle">Triangle</option>
                      <option value="yen">Yen</option>
                      <option value="local_mean">Local Mean</option>
                      <option value="local_gaussian">Local Gaussian</option>
                    </select>
                    </div>
                    <label className="checkbox">
                      <input type="checkbox" checked={fornmaFindLow} onChange={(e) => setFornmaFindLow(e.target.checked)} />
                      Find low-intensity nuclei <Tip text="Extra pass to recover missed nuclei in low-intensity regions." />
                    </label>
                    <label className="checkbox">
                      <input type="checkbox" checked={fornmaWeakly} onChange={(e) => setFornmaWeakly(e.target.checked)} />
                      Weakly labeled images <Tip text="Enable additional handling for weak staining/unclear contours." />
                    </label>
                  </>
                ) : (
                  <>
                    <h4 className="seg-subtitle">Nuclear Cellpose Parameters</h4>
                    <div className="field-head">Model <Tip text="Pretrained Cellpose model. If nuclei misses objects, try cyto3, cyto2, or cyto." /></div>
                    <div className="seg-threshold-wrap">
                      <select className="input seg-threshold-input" value={cellposeModel} onChange={(e) => setCellposeModel(e.target.value)}>
                        <option value="nuclei">nuclei</option>
                        <option value="cyto3">cyto3</option>
                        <option value="cyto2">cyto2</option>
                        <option value="cyto">cyto</option>
                      </select>
                    </div>
                    <div className="field-head">Diameter (px) <Tip text="Typical cell diameter in pixels for Cellpose scale normalization." /></div>
                    <input className="input" type="number" value={cellposeDiameter} onChange={(e) => setCellposeDiameter(e.target.value)} />
                    <div className="field-head">Flow Threshold <Tip text="Maximum flow error allowed; lower values are stricter." /></div>
                    <input className="input" type="number" value={cellposeFlow} onChange={(e) => setCellposeFlow(e.target.value)} step="0.05" />
                    <div className="field-head">Cellprob Threshold <Tip text="Cell probability threshold; lower values include more cells." /></div>
                    <input className="input" type="number" value={cellposeCellprob} onChange={(e) => setCellposeCellprob(e.target.value)} step="0.5" />
                    <label className="checkbox">
                      <input type="checkbox" checked={cellposeUseGpu} onChange={(e) => setCellposeUseGpu(e.target.checked)} />
                      Use GPU <Tip text="Enable GPU acceleration if available." />
                    </label>
                    <label className="checkbox">
                      <input type="checkbox" checked={cellposeInvert} onChange={(e) => setCellposeInvert(e.target.checked)} />
                      Invert Intensities <Tip text="Invert image values before segmentation when needed." />
                    </label>
                  </>
                )}
                <h4 className="seg-subtitle">Advanced Filters</h4>
                <label className="checkbox">
                  <input type="checkbox" checked={advEnable.shape} onChange={(e) => setAdvToggle("shape", e.target.checked)} />
                  Shape <Tip text="Filter nuclear masks by irregularity/shape metric." />
                </label>
                {advEnable.shape && <input className="input" type="number" step="0.01" value={advValues.shape} onChange={(e) => setAdvValue("shape", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={advEnable.eccentricity} onChange={(e) => setAdvToggle("eccentricity", e.target.checked)} />
                  Eccentricity <Tip text="Filter nuclear masks by elongation." />
                </label>
                {advEnable.eccentricity && <input className="input" type="number" step="0.01" value={advValues.eccentricity} onChange={(e) => setAdvValue("eccentricity", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={advEnable.min_size} onChange={(e) => setAdvToggle("min_size", e.target.checked)} />
                  Min Size <Tip text="Minimum nuclear mask area." />
                </label>
                {advEnable.min_size && <input className="input" type="number" step="1" value={advValues.min_size} onChange={(e) => setAdvValue("min_size", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={advEnable.max_size} onChange={(e) => setAdvToggle("max_size", e.target.checked)} />
                  Max Size <Tip text="Maximum nuclear mask area." />
                </label>
                {advEnable.max_size && <input className="input" type="number" step="1" value={advValues.max_size} onChange={(e) => setAdvValue("max_size", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={advEnable.min_radius} onChange={(e) => setAdvToggle("min_radius", e.target.checked)} />
                  Min Radius <Tip text="Minimum nuclear mask radius." />
                </label>
                {advEnable.min_radius && <input className="input" type="number" step="1" value={advValues.min_radius} onChange={(e) => setAdvValue("min_radius", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={advEnable.max_radius} onChange={(e) => setAdvToggle("max_radius", e.target.checked)} />
                  Max Radius <Tip text="Maximum nuclear mask radius." />
                </label>
                {advEnable.max_radius && <input className="input" type="number" step="1" value={advValues.max_radius} onChange={(e) => setAdvValue("max_radius", e.target.value)} />}
                </div>
              </details>
            )}
            {segmentationTarget !== "nucleus" && (
              <details open className="seg-compartment seg-compartment-cyto">
                <summary>Cytoplasm Segmentation</summary>
                <div className="seg-compartment-body">
                <label className="checkbox">
                  <input type="checkbox" checked={cytoRescaleIntensity} onChange={(e) => setCytoRescaleIntensity(e.target.checked)} />
                  Rescale Intensity <Tip text="Normalize intensity values before cytoplasm segmentation." />
                </label>
                <label className="checkbox">
                  <input type="checkbox" checked={cytoRemoveBackground} onChange={(e) => setCytoRemoveBackground(e.target.checked)} />
                  Remove Background <Tip text="Subtract smooth background before cytoplasm segmentation." />
                </label>
                {cytoRemoveBackground && (
                  <>
                    <div className="field-head">Rolling Radius (px) <Tip text="Radius used for background removal before cytoplasm segmentation." /></div>
                    <input className="input" type="number" value={cytoRollingRadius} onChange={(e) => setCytoRollingRadius(e.target.value)} />
                  </>
                )}
                <div className="field-head">Model <Tip text="Pretrained Cellpose model used for cytoplasm segmentation. For visible-light or brightfield cells, start with cyto3." /></div>
                <div className="seg-threshold-wrap">
                  <select className="input seg-threshold-input" value={cytoCellposeModel} onChange={(e) => setCytoCellposeModel(e.target.value)}>
                    <option value="cyto3">cyto3</option>
                    <option value="cyto2">cyto2</option>
                    <option value="cyto">cyto</option>
                    <option value="nuclei">nuclei</option>
                  </select>
                </div>
                <div className="field-head">Diameter (px) <Tip text="Typical cytoplasm/cell diameter in pixels for Cellpose scale normalization." /></div>
                <input className="input" type="number" value={cytoCellposeDiameter} onChange={(e) => setCytoCellposeDiameter(e.target.value)} />
                <div className="field-head">Flow Threshold <Tip text="Maximum flow error allowed; lower values are stricter. For visible-light or brightfield cells, try 0.6-0.8." /></div>
                <input className="input" type="number" value={cytoCellposeFlow} onChange={(e) => setCytoCellposeFlow(e.target.value)} step="0.05" />
                <div className="field-head">Cellprob Threshold <Tip text="Cell probability threshold; lower values include more cells. For visible-light or brightfield cells, try -3 or -4." /></div>
                <input className="input" type="number" value={cytoCellposeCellprob} onChange={(e) => setCytoCellposeCellprob(e.target.value)} step="0.5" />
                <label className="checkbox">
                  <input type="checkbox" checked={cellposeUseGpu} onChange={(e) => setCellposeUseGpu(e.target.checked)} />
                  Use GPU <Tip text="Enable GPU acceleration if available." />
                </label>
                <label className="checkbox">
                  <input type="checkbox" checked={cytoCellposeInvert} onChange={(e) => setCytoCellposeInvert(e.target.checked)} />
                  Invert Intensities <Tip text="Invert image values before segmentation when needed." />
                </label>
                <h4 className="seg-subtitle">Advanced Filters</h4>
                <label className="checkbox">
                  <input type="checkbox" checked={cytoAdvEnable.shape} onChange={(e) => setCytoAdvToggle("shape", e.target.checked)} />
                  Shape <Tip text="Filter cytoplasm masks by irregularity/shape metric." />
                </label>
                {cytoAdvEnable.shape && <input className="input" type="number" step="0.01" value={cytoAdvValues.shape} onChange={(e) => setCytoAdvValue("shape", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={cytoAdvEnable.eccentricity} onChange={(e) => setCytoAdvToggle("eccentricity", e.target.checked)} />
                  Eccentricity <Tip text="Filter cytoplasm masks by elongation." />
                </label>
                {cytoAdvEnable.eccentricity && <input className="input" type="number" step="0.01" value={cytoAdvValues.eccentricity} onChange={(e) => setCytoAdvValue("eccentricity", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={cytoAdvEnable.min_size} onChange={(e) => setCytoAdvToggle("min_size", e.target.checked)} />
                  Min Size <Tip text="Minimum cytoplasm mask area." />
                </label>
                {cytoAdvEnable.min_size && <input className="input" type="number" step="1" value={cytoAdvValues.min_size} onChange={(e) => setCytoAdvValue("min_size", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={cytoAdvEnable.max_size} onChange={(e) => setCytoAdvToggle("max_size", e.target.checked)} />
                  Max Size <Tip text="Maximum cytoplasm mask area." />
                </label>
                {cytoAdvEnable.max_size && <input className="input" type="number" step="1" value={cytoAdvValues.max_size} onChange={(e) => setCytoAdvValue("max_size", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={cytoAdvEnable.min_radius} onChange={(e) => setCytoAdvToggle("min_radius", e.target.checked)} />
                  Min Radius <Tip text="Minimum cytoplasm mask radius." />
                </label>
                {cytoAdvEnable.min_radius && <input className="input" type="number" step="1" value={cytoAdvValues.min_radius} onChange={(e) => setCytoAdvValue("min_radius", e.target.value)} />}
                <label className="checkbox">
                  <input type="checkbox" checked={cytoAdvEnable.max_radius} onChange={(e) => setCytoAdvToggle("max_radius", e.target.checked)} />
                  Max Radius <Tip text="Maximum cytoplasm mask radius." />
                </label>
                {cytoAdvEnable.max_radius && <input className="input" type="number" step="1" value={cytoAdvValues.max_radius} onChange={(e) => setCytoAdvValue("max_radius", e.target.value)} />}
                </div>
              </details>
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Channel Settings</summary>
          <div className="seg-body">
            {channels.length === 0 ? (
              <p className="hint">No channels loaded yet. Use Load images and save the table.</p>
            ) : (
              channels.map((ch) => {
                const cfg = channelCfg[ch.id] || {};
                const showRing = cytoEnabled && cytoChannels.includes(ch.id);
                const showFoci = fociEnabled && fociChannels.includes(ch.id);
                return (
                  <details key={`ch-settings-${ch.id}`} className="seg-section">
                    <summary>{ch.name}</summary>
                    <div className="seg-body">
                      <h4 className="seg-subtitle">Measurement Compartments</h4>
                      {segmentationTarget !== "cytoplasm" && (
                        <label className="checkbox">
                          <input
                            type="checkbox"
                            checked={!!cfg.measure_nucleus}
                            onChange={(e) => setChCfg(ch.id, { measure_nucleus: e.target.checked })}
                          />
                          Measure nucleus <Tip text="Measure this channel using nuclear contours." />
                        </label>
                      )}
                      {segmentationTarget !== "nucleus" && (
                        <label className="checkbox">
                          <input
                            type="checkbox"
                            checked={segmentationTarget === "cytoplasm" ? true : !!cfg.measure_cytoplasm}
                            disabled={segmentationTarget === "cytoplasm"}
                            onChange={(e) => setChCfg(ch.id, { measure_cytoplasm: e.target.checked })}
                          />
                          Measure cytoplasm <Tip text="Measure this channel using cytoplasm contours." />
                        </label>
                      )}

                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={!!cfg.rescale_intensity}
                          onChange={(e) => setChCfg(ch.id, { rescale_intensity: e.target.checked })}
                        />
                        Rescale intensity <Tip text="Re-distributes channel intensity values to improve contrast." />
                      </label>

                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={!!cfg.remove_background}
                          onChange={(e) => setChCfg(ch.id, { remove_background: e.target.checked })}
                        />
                        Remove background <Tip text="Apply rolling-ball background subtraction in this channel." />
                      </label>
                      {cfg.remove_background && (
                        <input
                          className="input"
                          type="number"
                          min="1"
                          step="1"
                          value={cfg.rolling_ball_radius ?? 40}
                          onChange={(e) => setChCfg(ch.id, { rolling_ball_radius: e.target.value })}
                          placeholder="Rolling-ball radius (px)"
                        />
                      )}

                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={!!cfg.match_histograms}
                          onChange={(e) => setChCfg(ch.id, { match_histograms: e.target.checked })}
                        />
                        Match histograms <Tip text="Normalize histogram across images for this channel." />
                      </label>

                      {showRing && (
                        <>
                          <h4 className="seg-subtitle">Cytoplasmatic Ring</h4>
                          <div className="field-head">Ring size (px) <Tip text="Width of cytoplasmatic ring for translocation measurement." /></div>
                          <input
                            className="input"
                            type="number"
                            min="1"
                            step="1"
                            value={cfg.ring_size ?? 3}
                            onChange={(e) => setChCfg(ch.id, { ring_size: e.target.value })}
                          />
                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={!!cfg.use_ellipse}
                              onChange={(e) => setChCfg(ch.id, { use_ellipse: e.target.checked })}
                            />
                            Use ellipse <Tip text="Use ellipse approximation for ring calculation." />
                          </label>
                        </>
                      )}

                      {showFoci && (
                        <>
                          <h4 className="seg-subtitle">Foci Detection</h4>
                          <div className="field-head">Min foci size (px²) <Tip text="Minimum foci area to keep." /></div>
                          <input
                            className="input"
                            type="number"
                            min="1"
                            step="1"
                            value={cfg.foci_min_size ?? 7}
                            onChange={(e) => setChCfg(ch.id, { foci_min_size: e.target.value })}
                          />

                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={!!cfg.foci_max_size_enable}
                              onChange={(e) => setChCfg(ch.id, { foci_max_size_enable: e.target.checked })}
                            />
                            Max foci size <Tip text="Enable to cap foci maximum area." />
                          </label>
                          {cfg.foci_max_size_enable && (
                            <input
                              className="input"
                              type="number"
                              min="1"
                              step="1"
                              value={cfg.foci_max_size ?? 20}
                              onChange={(e) => setChCfg(ch.id, { foci_max_size: e.target.value })}
                            />
                          )}

                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={!!cfg.foci_min_int_enable}
                              onChange={(e) => setChCfg(ch.id, { foci_min_int_enable: e.target.checked })}
                            />
                            Min foci intensity <Tip text="Enable to enforce minimum spot intensity." />
                          </label>
                          {cfg.foci_min_int_enable && (
                            <input
                              className="input"
                              type="number"
                              step="0.1"
                              value={cfg.foci_min_int ?? 0}
                              onChange={(e) => setChCfg(ch.id, { foci_min_int: e.target.value })}
                            />
                          )}

                          <label className="checkbox">
                            <input
                              type="checkbox"
                              checked={!!cfg.foci_max_int_enable}
                              onChange={(e) => setChCfg(ch.id, { foci_max_int_enable: e.target.checked })}
                            />
                            Max foci intensity <Tip text="Enable to cap spot intensity." />
                          </label>
                          {cfg.foci_max_int_enable && (
                            <input
                              className="input"
                              type="number"
                              step="0.1"
                              value={cfg.foci_max_int ?? 1}
                              onChange={(e) => setChCfg(ch.id, { foci_max_int: e.target.value })}
                            />
                          )}

                          <div className="field-head">Foci prominence <Tip text="How much a spot must stand out from background." /></div>
                          <input
                            className="input"
                            type="number"
                            step="0.1"
                            min="0"
                            value={cfg.foci_prominence ?? 1.2}
                            onChange={(e) => setChCfg(ch.id, { foci_prominence: e.target.value })}
                          />
                        </>
                      )}
                    </div>
                  </details>
                );
              })
            )}
          </div>
        </details>
      </div>

      <div className="seg-footer">
        <button className="secondary" onClick={() => startSeg(true)} disabled={segRunning}>Preview</button>
        <button className="primary" onClick={() => startSeg(false)} disabled={segRunning}>Run</button>
        <button className="danger" onClick={() => onStopSegmentation()} disabled={!segRunning || segCanceling}>
          {segCanceling ? "Stopping..." : "Stop"}
        </button>
        {segCanceling && <span className="seg-stop-state" role="status">Finishing current image and stopping.</span>}
        {segCanceled && <span className="seg-stop-state stopped" role="status">Stopped. No further images will be processed.</span>}
      </div>
    </Card>
    {modalOpen && (
      <div className="seg-modal-backdrop" onClick={() => setModalOpen(false)}>
        <div className="seg-modal" onClick={(e) => e.stopPropagation()}>
          <div className="seg-modal-header">
            <h4>Load images — conditions × channels</h4>
          </div>
          <div className="seg-modal-body">
            {modalError && <div className="seg-modal-error">{modalError}</div>}
            <div className="seg-load-table-wrap">
              <table className="seg-load-table">
                <thead>
                  <tr>
                    <th>Condition</th>
                    {channels.map((ch) => (
                      <th key={`h-${ch.id}`}>
                        <div className="row row-between">
                          <input
                            className="input"
                            value={ch.name}
                            onChange={(e) => updateChannelName(ch.id, e.target.value)}
                            placeholder="Channel name"
                          />
                          <button
                            className="ghost btn-small"
                            onClick={() => removeChannel(ch.id)}
                            disabled={channels.length <= 1}
                            title="Remove channel"
                          >
                            Remove
                          </button>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(imagesData.rows || []).map((row, rIdx) => (
                    <tr key={`r-${rIdx}`}>
                      <td>
                        <div className="row row-between">
                          <input
                            className="input"
                            value={row.condition || ""}
                            onChange={(e) => updateCondition(rIdx, e.target.value)}
                            placeholder="Condition name"
                          />
                          <button
                            className="ghost btn-small"
                            onClick={() => removeCondition(rIdx)}
                            disabled={(imagesData.rows || []).length <= 1}
                            title="Remove condition"
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                      {channels.map((ch, cIdx) => (
                        <td key={`c-${rIdx}-${ch.id}`}>
                          <div className="row path-row">
                            <input
                              className="input"
                              value={row[ch.id] || ""}
                              onChange={(e) => updatePathCell(rIdx, ch.id, e.target.value)}
                              placeholder={`Path to ${ch.name}`}
                            />
                        <button className="secondary btn-small" onClick={() => browsePathCell(rIdx, ch.id)}><BrowseLabel>Browse</BrowseLabel></button>
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="seg-modal-footer">
            <span className="hint">{counterText}</span>
            <button className="ghost" onClick={addCondition}>+ Add condition</button>
            <button className="ghost" onClick={addChannel}>+ Add channel</button>
            <button className="primary" onClick={saveImagesTable}>Save</button>
            <button className="secondary" onClick={() => setModalOpen(false)}>Close</button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}

function RegistrationLeftPanel({ onPickDirectory, onStartRegistration, onStopRegistration, regJob }) {
  const [savePath, setSavePath] = useState("");
  const [imagesData, setImagesData] = useState({
    channels: [{ id: "ch1", name: "Channel 1" }],
    rows: [{ condition: "Control", ch1: "" }],
  });
  const [modalOpen, setModalOpen] = useState(false);
  const [modalError, setModalError] = useState("");
  const [summaryText, setSummaryText] = useState("No images loaded yet.");
  const [referenceChannel, setReferenceChannel] = useState("");
  const [movingChannels, setMovingChannels] = useState([]);
  const [cropOutput, setCropOutput] = useState(true);

  const channels = imagesData.channels || [];
  const channelIds = new Set(channels.map((c) => c.id));
  const regRunning = ["starting", "queued", "running", "canceling"].includes(regJob?.status || "idle");

  useEffect(() => {
    if (channels.length === 0) return;
    if (!channelIds.has(referenceChannel)) {
      setReferenceChannel(channels[0].id);
    }
    setMovingChannels((prev) => prev.filter((id) => channelIds.has(id) && id !== referenceChannel));
  }, [imagesData.channels, referenceChannel]);

  const addCondition = () => {
    setImagesData((prev) => {
      const row = { condition: "" };
      (prev.channels || []).forEach((ch) => { row[ch.id] = ""; });
      return { ...prev, rows: [...(prev.rows || []), row] };
    });
  };

  const addChannel = () => {
    setImagesData((prev) => {
      const maxIdx = Math.max(0, ...(prev.channels || []).map((ch) => Number((ch.id || "").replace("ch", "")) || 0));
      const newId = `ch${maxIdx + 1}`;
      const nextChannels = [...(prev.channels || []), { id: newId, name: `Channel ${maxIdx + 1}` }];
      const nextRows = (prev.rows || []).map((r) => ({ ...r, [newId]: "" }));
      return { ...prev, channels: nextChannels, rows: nextRows };
    });
  };

  const removeCondition = (rowIdx) => {
    setImagesData((prev) => ({ ...prev, rows: (prev.rows || []).filter((_, i) => i !== rowIdx) }));
  };

  const removeChannel = (chId) => {
    setImagesData((prev) => {
      const nextChannels = (prev.channels || []).filter((ch) => ch.id !== chId);
      const nextRows = (prev.rows || []).map((r) => {
        const copy = { ...r };
        delete copy[chId];
        return copy;
      });
      return { ...prev, channels: nextChannels, rows: nextRows };
    });
    if (referenceChannel === chId) setReferenceChannel("");
    setMovingChannels((prev) => prev.filter((id) => id !== chId));
  };

  const updateChannelName = (chId, name) => {
    setImagesData((prev) => ({
      ...prev,
      channels: (prev.channels || []).map((ch) => (ch.id === chId ? { ...ch, name } : ch)),
    }));
  };

  const updateCondition = (rowIdx, condition) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).map((r, i) => (i === rowIdx ? { ...r, condition } : r)),
    }));
  };

  const updatePathCell = (rowIdx, chId, path) => {
    setImagesData((prev) => ({
      ...prev,
      rows: (prev.rows || []).map((r, i) => (i === rowIdx ? { ...r, [chId]: path } : r)),
    }));
  };

  const browsePathCell = async (rowIdx, chId) => {
    const picked = await onPickDirectory();
    if (!picked) return;
    updatePathCell(rowIdx, chId, picked);
  };

  const saveImagesTable = () => {
    const errors = [];
    const chs = imagesData.channels || [];
    const rows = imagesData.rows || [];

    const normalizedChannels = chs.map((ch, idx) => ({ ...ch, name: channelNameOrDefault(ch, idx) }));
    const chNames = normalizedChannels.map((c) => c.name);
    if (new Set(chNames).size !== chNames.length) errors.push("Each channel needs a unique name. Rename duplicate channel columns before saving.");

    const conds = rows.map((r) => (r.condition || "").trim());
    if (conds.some((c) => !c)) errors.push("Each row needs a condition name, for example Control or Treatment.");
    if (new Set(conds).size !== conds.length) errors.push("Each condition name must be unique. Rename duplicate rows before saving.");

    rows.forEach((r, idx) => {
      normalizedChannels.forEach((ch) => {
        const p = (r[ch.id] || "").trim();
        if (!p) errors.push(`Row ${idx + 1}, ${ch.name}: choose the image folder for this condition/channel cell.`);
      });
    });

    if (errors.length) {
      setModalError(errors.join("\n"));
      return;
    }

    const lines = [`Image selection OK:`, `Conditions: ${rows.length} | Channels: ${chs.length}`, ""];
    rows.forEach((r) => {
      lines.push(`- ${r.condition}:`);
      normalizedChannels.forEach((ch) => lines.push(`    ${ch.name}: ${r[ch.id] || ""}`));
    });
    setImagesData((prev) => ({ ...prev, channels: normalizedChannels }));
    setSummaryText(lines.join("\n"));
    setModalError("");
    setModalOpen(false);
  };

  const startRegistration = async () => {
    await onStartRegistration({
      images_data: imagesData,
      reg_data: {
        save_path: savePath,
        reference: referenceChannel,
        moving: movingChannels,
        crop: !!cropOutput,
      },
    });
  };

  const counterText = `Channels: ${channels.length} | Conditions: ${(imagesData.rows || []).length}`;

  return (
    <>
      <Card as="aside" className="panel seg-panel" variant="panel">
        <div className="seg-header">
          <h3>Image Registration Settings</h3>
          <p className="hint">Set the reference channel, optional moving channels, and output options for registration.</p>
        </div>

        <div className="seg-scroll">
          <div className="sidebar-control-block">
          <button className="secondary" title="Open the condition-by-channel table used to define the registration inputs." onClick={() => { setModalError(""); setModalOpen(true); }}>Load images</button>
          <div className="field-head">Saving path <Tip text="Directory where registered outputs will be saved." /></div>
          <div className="row path-row">
            <input className="input" value={savePath} onChange={(e) => setSavePath(e.target.value)} placeholder="Folder to save results..." />
            <button className="secondary" title="Choose where registration outputs should be written." onClick={async () => {
              const p = await onPickDirectory();
              if (p) setSavePath(p);
            }}><BrowseLabel>Browse</BrowseLabel></button>
          </div>
          <details className="seg-summary">
            <summary>Image selection summary</summary>
            <pre>{summaryText}</pre>
          </details>
          </div>
          <details open className="seg-section">
            <summary>Channel mapping</summary>
            <div className="seg-body">
              <div className="field-head">Reference channel <Tip text="Fixed channel used as the alignment target for all corrected channels." /></div>
              <select className="input" value={referenceChannel} onChange={(e) => setReferenceChannel(e.target.value)}>
                <option value="">Select reference...</option>
                {channels.map((ch) => <option key={`reg-ref-${ch.id}`} value={ch.id}>{ch.name}</option>)}
              </select>
              <div className="field-head">Other channels to correct <Tip text="Optional. Select any extra channels that should be transformed to match the reference channel. Leave empty to register only the reference channel over time." /></div>
              <div className="multi-picker">
                {channels.filter((ch) => ch.id !== referenceChannel).map((ch) => (
                  <label className="checkbox" key={`reg-m-${ch.id}`}>
                    <input
                      type="checkbox"
                      checked={movingChannels.includes(ch.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setMovingChannels((prev) => Array.from(new Set([...prev, ch.id])));
                        } else {
                          setMovingChannels((prev) => prev.filter((id) => id !== ch.id));
                        }
                      }}
                    />
                    {ch.name}
                  </label>
                ))}
                {channels.filter((ch) => ch.id !== referenceChannel).length === 0 && (
                  <p className="hint">Only one channel is loaded. Registration will run on the reference channel only.</p>
                )}
              </div>
            </div>
          </details>

          <details open className="seg-section">
            <summary>Options</summary>
            <div className="seg-body">
              <label className="checkbox">
                <input type="checkbox" checked={cropOutput} onChange={(e) => setCropOutput(e.target.checked)} />
                Crop output (keep common FOV) <Tip text="Trim the output to the common overlapping field of view after registration." />
              </label>
            </div>
          </details>

        </div>

        <div className="seg-footer">
          <button className="primary" title="Run image registration with the current mapping and options." onClick={startRegistration} disabled={regRunning}>Run Registration</button>
          <button className="danger" title="Request cancellation of the current registration job." onClick={() => onStopRegistration()} disabled={!regRunning}>Stop</button>
        </div>
      </Card>

      {modalOpen && (
        <div className="seg-modal-backdrop" onClick={() => setModalOpen(false)}>
          <div className="seg-modal" onClick={(e) => e.stopPropagation()}>
            <div className="seg-modal-header"><h4>Load images — conditions × channels</h4></div>
            <div className="seg-modal-body">
              {modalError && <div className="seg-modal-error">{modalError}</div>}
              <div className="seg-load-table-wrap">
                <table className="seg-load-table">
                  <thead>
                    <tr>
                      <th>Condition</th>
                      {channels.map((ch) => (
                        <th key={`h-reg-${ch.id}`}>
                          <div className="row row-between">
                            <input className="input" value={ch.name} onChange={(e) => updateChannelName(ch.id, e.target.value)} placeholder="Channel name" />
                            <button className="ghost btn-small" onClick={() => {
                              if (confirmRemoveFilled(ch, `Channel ${cIdx + 1}`)) removeChannel(ch.id);
                            }} disabled={channels.length <= 1}>Remove</button>
                          </div>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(imagesData.rows || []).map((row, rIdx) => (
                      <tr key={`reg-r-${rIdx}`}>
                        <td>
                          <div className="row row-between">
                            <input className="input" value={row.condition || ""} onChange={(e) => updateCondition(rIdx, e.target.value)} placeholder="Condition name" />
                            <button className="ghost btn-small" onClick={() => {
                              if (confirmRemoveFilled(row, `Condition ${rIdx + 1}`)) removeCondition(rIdx);
                            }} disabled={(imagesData.rows || []).length <= 1}>Remove</button>
                          </div>
                        </td>
                        {channels.map((ch) => (
                          <td key={`reg-c-${rIdx}-${ch.id}`}>
                            <div className="row path-row">
                              <input className="input" value={row[ch.id] || ""} onChange={(e) => updatePathCell(rIdx, ch.id, e.target.value)} placeholder={`Path to ${ch.name}`} />
                              <button className="secondary btn-small" onClick={() => browsePathCell(rIdx, ch.id)}><BrowseLabel>Browse</BrowseLabel></button>
                            </div>
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="seg-modal-footer">
              <span className="hint">{counterText}</span>
              <button className="ghost" onClick={addCondition}>+ Add condition</button>
              <button className="ghost" onClick={addChannel}>+ Add channel</button>
              <button className="primary" onClick={saveImagesTable}>Save</button>
              <button className="secondary" onClick={() => setModalOpen(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function FociOverlayLeftPanel({ onPickDirectory, onStartFoci, onStopFoci, onLoadFociChannels, fociJob }) {
  const [pklPath, setPklPath] = useState("");
  const [savePath, setSavePath] = useState("");
  const [channelsOptions, setChannelsOptions] = useState([]);
  const [channels, setChannels] = useState([]);
  const [actions, setActions] = useState(["overlay"]);
  const [saveImages, setSaveImages] = useState(true);
  const running = ["starting", "queued", "running", "canceling"].includes(fociJob?.status || "idle");

  const loadChannels = async (path) => {
    if (!path?.trim()) {
      setChannelsOptions([]);
      setChannels([]);
      return;
    }
    try {
      const opts = await onLoadFociChannels(path.trim());
      setChannelsOptions(opts);
      setChannels(opts.map((o) => o.value));
    } catch {
      setChannelsOptions([]);
      setChannels([]);
    }
  };

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Foci Overlay Settings</h3>
        <p className="hint">Generate overlay views and profile outputs from previously processed `.pkl` files.</p>
      </div>

      <div className="seg-scroll">
        <div className="sidebar-control-block">
        <div className="field-head">Pickle (.pkl) folder <Tip text="Folder containing the `.pkl` files used to generate the selected foci outputs." /></div>
        <div className="row path-row">
          <input className="input" value={pklPath} onChange={(e) => setPklPath(e.target.value)} placeholder="Folder with .pkl result files..." />
          <button className="secondary" title="Choose the folder containing the `.pkl` files." onClick={async () => {
            const p = await onPickDirectory();
            if (p) {
              setPklPath(p);
              await loadChannels(p);
            }
          }}><BrowseLabel>Browse</BrowseLabel></button>
        </div>
        <div className="field-head">Saving path <Tip text="Directory where the overlay outputs and optional rendered images will be saved." /></div>
        <div className="row path-row">
          <input className="input" value={savePath} onChange={(e) => setSavePath(e.target.value)} placeholder="Folder to save overlay outputs..." />
          <button className="secondary" title="Choose where the foci overlay outputs should be written." onClick={async () => {
            const p = await onPickDirectory();
            if (p) setSavePath(p);
          }}><BrowseLabel>Browse</BrowseLabel></button>
        </div>
        </div>
        <details open className="seg-section">
          <summary>Channels</summary>
          <div className="seg-body">
            {channelsOptions.length === 0 ? (
              <p className="hint">Point to a .pkl folder to load channels automatically.</p>
            ) : (
              <div className="multi-picker">
                {channelsOptions.map((opt) => (
                  <label className="checkbox" key={`foci-ch-${opt.value}`}>
                    <input
                      type="checkbox"
                      checked={channels.includes(opt.value)}
                      onChange={(e) => {
                        if (e.target.checked) setChannels((prev) => Array.from(new Set([...prev, opt.value])));
                        else setChannels((prev) => prev.filter((v) => v !== opt.value));
                      }}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Actions</summary>
          <div className="seg-body">
            <label className="checkbox">
              <input
                type="checkbox"
                checked={actions.includes("overlay")}
                onChange={(e) => {
                  if (e.target.checked) setActions((prev) => Array.from(new Set([...prev, "overlay"])));
                  else setActions((prev) => prev.filter((a) => a !== "overlay"));
                }}
              />
              Overlay <Tip text="Generate overlay views showing the detected foci over the original image context." />
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={actions.includes("profiles")}
                onChange={(e) => {
                  if (e.target.checked) setActions((prev) => Array.from(new Set([...prev, "profiles"])));
                  else setActions((prev) => prev.filter((a) => a !== "profiles"));
                }}
              />
              Plot profiles <Tip text="Generate profile-style output plots from the loaded foci measurements." />
            </label>
            <label className="checkbox">
              <input type="checkbox" checked={saveImages} onChange={(e) => setSaveImages(e.target.checked)} />
              Save overlay images <Tip text="Export the rendered overlay images in addition to the other selected outputs." />
            </label>
          </div>
        </details>

      </div>

      <div className="seg-footer">
        <button
          className="primary"
          title="Run the selected foci overlay/profile outputs with the chosen channels and save options."
          onClick={() => onStartFoci({
            pkl_path: pklPath.trim(),
            save_path: (savePath.trim() || pklPath.trim()),
            channels,
            actions,
            save_images: !!saveImages,
          })}
          disabled={running}
        >
          Run Overlay
        </button>
        <button className="danger" title="Request cancellation of the current foci overlay job." onClick={() => onStopFoci()} disabled={!running}>Stop</button>
      </div>
    </Card>
  );
}

function PlotDataLeftPanel({ onPickCsv, onPreview, status, setStatusExternal, graphState, setGraphState, loading }) {
  const graphTypes = ["scatter", "violin", "box", "dot", "bar", "line", "cpd"];
  const [collapsedDatasets, setCollapsedDatasets] = React.useState({});

  const setField = (k, v) => setGraphState((prev) => ({ ...prev, [k]: v }));
  const addDataset = () => setField("datasets", [...(graphState.datasets || []), { id: makeRowId(), name: `Dataset ${(graphState.datasets || []).length + 1}`, path: "", columns: null, enabled: true }]);
  const removeDataset = (id) => setField("datasets", (graphState.datasets || []).filter((d) => d.id !== id));
  const updateDataset = (id, patch) => setField("datasets", (graphState.datasets || []).map((d) => (d.id === id ? { ...d, ...patch } : d)));
  const toggleDataset = (id) => setCollapsedDatasets((prev) => ({ ...prev, [id]: !prev[id] }));

  const cols = graphState.columns || [];
  const categoricalCols = graphState.categoricalColumns || [];
  const canPreview = (graphState.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim()) && !graphState.columnsWarning;
  const graphType = graphState.graph_type || "scatter";
  const requiresXY = PLOT_TYPES_REQUIRE_XY.has(graphType);
  const requiresY = PLOT_TYPES_REQUIRE_Y.has(graphType);
  const supportsDot = PLOT_TYPES_SUPPORT_DOT.has(graphType);
  const supportsSize = PLOT_TYPES_SUPPORT_SIZE.has(graphType);
  const supportsX = PLOT_TYPES_SUPPORT_X.has(graphType);
  const xOptions = (graphType === "violin" || graphType === "box" || graphType === "dot" || graphType === "bar") ? categoricalCols : cols;
  const lineRolling = graphType === "line" && !!graphState.line_rolling;
  const isCpd = graphType === "cpd";
  const shouldShowFrames = isCpd || (graphType === "line" && (!graphState.x || graphState.x === "Frame"));

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Plot Data Settings</h3>
        <p className="hint">Use CSV outputs to build interactive plots.</p>
      </div>
      <div className="seg-scroll">
        <div className="dataset-list">
            {(graphState.datasets || []).map((d, idx) => (
              <div className="dataset" key={d.id}>
                <div className="row dataset-header-row">
                  <DatasetCollapseButton collapsed={!!collapsedDatasets[d.id]} onClick={() => toggleDataset(d.id)} label={d.name || `Dataset ${idx + 1}`} />
                  <div className="dataset-title">{d.name?.trim() || `Dataset ${idx + 1}`}</div>
                  {(graphState.datasets || []).length > 1 && (
                    <button className="ghost btn-small" title="Remove this dataset from the plotting configuration." onClick={() => {
                      if (confirmRemoveFilled(d, `Dataset ${idx + 1}`)) removeDataset(d.id);
                    }}>Remove</button>
                  )}
                  <DatasetBadge>#{idx + 1}</DatasetBadge>
                </div>
                {!collapsedDatasets[d.id] && (
                  <>
                    <div className="row">
                      <label className="checkbox" style={{ minWidth: 62 }}>
                        <input
                          type="checkbox"
                          checked={d.enabled !== false}
                          onChange={(e) => updateDataset(d.id, { enabled: e.target.checked })}
                        />
                        plot
                      </label>
                      <div style={{ flex: 1 }}>
                        <div className="field-head">Dataset name <Tip text="Friendly label used in legends and plot summaries." /></div>
                        <input
                          className="input"
                          value={d.name || ""}
                          onChange={(e) => updateDataset(d.id, { name: e.target.value })}
                          placeholder={`Dataset ${idx + 1} name`}
                        />
                      </div>
                    </div>
                    <div className="row path-row">
                      <div style={{ flex: 1 }}>
                        <div className="field-head">CSV path <Tip text="Local CSV file containing the measurements to plot." /></div>
                        <input className="input" value={d.path || ""} onChange={(e) => updateDataset(d.id, { path: e.target.value })} placeholder="/path/Results.csv" />
                      </div>
                      <button
                        className="secondary"
                        title="Choose a CSV file for this plot dataset."
                        onClick={async () => {
                          try {
                            const picked = await onPickCsv();
                            if (picked) updateDataset(d.id, { path: picked, name: (d.name || "").trim() ? d.name : String(picked).split("/").pop() || d.name });
                          } catch (err) {
                            setStatusExternal(errorMessageFromException(err, "Could not open the CSV picker. Check that the backend is running and try again."), "error");
                          }
                        }}
                      >
                        <BrowseLabel>Browse CSV</BrowseLabel>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
            <button className="secondary add-dataset-button" title="Add another CSV dataset to the plot configuration." onClick={addDataset}>Add dataset</button>
            {graphState.columnsWarning && (
              <Status level="error" text={graphState.columnsWarning} />
            )}
        </div>

        <details open className="seg-section">
          <summary>Plot options</summary>
          <div className="seg-body">
            <div className="field-head">Graph type <Tip text="Select the plot style to generate from the loaded datasets." /></div>
            <select
              className="input"
              value={graphState.graph_type}
              onChange={(e) => {
                const nextType = e.target.value;
                setGraphState((prev) => ({
                  ...prev,
                  graph_type: nextType,
                  x: PLOT_TYPES_SUPPORT_X.has(nextType) ? prev.x : "",
                  size: PLOT_TYPES_SUPPORT_SIZE.has(nextType) ? prev.size : "",
                  line_rolling: nextType === "line" ? prev.line_rolling : false,
                }));
              }}
            >
              {graphTypes.map((g) => <option key={`gt-${g}`} value={g}>{g}</option>)}
            </select>
            {!isCpd && supportsX && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">X axis <Tip text="Column used on the horizontal axis of the selected plot type." /></div>
                  <select className="input" value={graphState.x} onChange={(e) => setField("x", e.target.value)}>
                  <option value="">
                    {(graphType === "violin" || graphType === "box" || graphType === "dot" || graphType === "bar")
                      ? "Category axis (optional)"
                      : (graphType === "line"
                        ? "X axis (default: Frame)"
                        : (requiresXY ? "Select X axis (required)" : "Select X axis"))}
                  </option>
                  {xOptions.map((c) => <option key={`x-${c}`} value={c}>{c}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Y axis <Tip text="Column used on the vertical axis of the selected plot type." /></div>
                  <select className="input" value={graphState.y} onChange={(e) => setField("y", e.target.value)}>
                  <option value="">{requiresY ? "Select Y axis (required)" : "Select Y axis"}</option>
                  {cols.map((c) => <option key={`y-${c}`} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
            )}
            {!isCpd && !supportsX && (
              <div>
                <div className="field-head">Y axis <Tip text="Column used on the vertical axis of the selected plot type." /></div>
                <select className="input" value={graphState.y} onChange={(e) => setField("y", e.target.value)}>
                  <option value="">{requiresY ? "Select Y axis (required)" : "Select Y axis"}</option>
                  {cols.map((c) => <option key={`y-${c}`} value={c}>{c}</option>)}
                </select>
              </div>
            )}
            {!isCpd && (
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Hue <Tip text="Optional column used to color points or groups in the plot." /></div>
                <select
                className="input"
                value={graphState.hue}
                onChange={(e) => setField("hue", e.target.value)}
              >
                <option value="">Hue (optional)</option>
                {cols.map((c) => <option key={`h-${c}`} value={c}>{c}</option>)}
              </select>
              </div>
              {supportsSize && (
                <div style={{ flex: 1 }}>
                  <div className="field-head">Size <Tip text="Optional numeric column used to scale marker size when supported." /></div>
                  <select className="input" value={graphState.size} onChange={(e) => setField("size", e.target.value)}>
                  <option value="">Size (optional)</option>
                  {cols.map((c) => <option key={`s-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              )}
            </div>
            )}
            {graphType === "violin" && (
              <>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={!!graphState.violin_box}
                    onChange={(e) => setField("violin_box", e.target.checked)}
                  />
                  Show box inside violin <Tip text="Overlay a boxplot summary inside each violin distribution." />
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={!!graphState.violin_points}
                    onChange={(e) => setField("violin_points", e.target.checked)}
                  />
                  Show dots <Tip text="Overlay the individual observations on top of the violin plot." />
                </label>
              </>
            )}
            {isCpd && (
              <div className="hint">
                CPD (Cumulative Population Doubling) estimates cumulative growth by summing doublings between consecutive frames:
                CPD = sum(log2(Nt+1 / Nt)). Use frames from different days/timepoints.
              </div>
            )}
            {shouldShowFrames && (
              <div>
                <div className="field-head">Frames <Tip text="Comma-separated list of frames/timepoints to include in the plot." /></div>
                <input
                  className="input"
                  value={graphState.framesText || ""}
                  onChange={(e) => setField("framesText", e.target.value)}
                  placeholder={isCpd ? "Frames (required, e.g. 0,1,2,3)" : "Frames (optional, empty = all)"}
                />
              </div>
            )}
            {isCpd && (
              <div>
                <div className="field-head">Control condition <Tip text="Optional control group used as a reference in CPD interpretation." /></div>
                <select
                  className="input"
                  value={graphState.control || ""}
                  onChange={(e) => setField("control", e.target.value)}
                >
                  <option value="">Control condition (optional)</option>
                  {(graphState.controlOptions || []).map((c) => (
                    <option key={`ctrl-${c}`} value={c}>{c}</option>
                  ))}
                </select>
              </div>
            )}
            {graphType === "line" && (
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={!!graphState.line_rolling}
                  onChange={(e) => setField("line_rolling", e.target.checked)}
                />
                Rolling average <Tip text="Smooth the line using a moving average window." />
              </label>
            )}
            {lineRolling && (
              <div>
                <div className="field-head">Rolling window <Tip text="Number of points used in the moving average for line plots." /></div>
                <input
                  className="input"
                  type="number"
                  min="1"
                  value={graphState.n ?? ""}
                  onChange={(e) => setField("n", e.target.value)}
                  placeholder="Rolling window n"
                />
              </div>
            )}
            {supportsDot && (
              <>
                <label className="checkbox">
                  <input type="checkbox" checked={!!graphState.dot} onChange={(e) => setField("dot", e.target.checked)} />
                  Dot (box) <Tip text="Overlay individual observations on the box plot." />
                </label>
                <label className="checkbox">
                  <input
                    type="checkbox"
                    checked={!!graphState.box_outliers}
                    onChange={(e) => setField("box_outliers", e.target.checked)}
                  />
                  Show outliers <Tip text="Display points considered outliers by the box plot rule." />
                </label>
              </>
            )}
            {graphType === "line" && (
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={!!graphState.compute_auc}
                  onChange={(e) => setField("compute_auc", e.target.checked)}
                />
                Compute AUC <Tip text="Calculate the area under the line curve when supported by the data." />
              </label>
            )}
          </div>
        </details>
      </div>
      <div className="seg-footer">
        <button
          className="primary"
          title="Generate the selected plot using the current datasets and plot options."
          onClick={onPreview}
          disabled={!canPreview || loading}
        >
          {loading ? "Generating..." : "Plot"}
        </button>
      </div>
      <Status level={status.level} text={status.text} />
    </Card>
  );
}

function ClusteringLeftPanel({ onPickCsv, onPreview, onElbow, status, loading, elbowLoading, state, setState }) {
  const [collapsedDatasets, setCollapsedDatasets] = React.useState({});
  const setField = (k, v) => setState((prev) => ({ ...prev, [k]: v }));
  const addDataset = () => setField("datasets", [...(state.datasets || []), { id: makeRowId(), name: `Dataset ${(state.datasets || []).length + 1}`, path: "", enabled: true }]);
  const removeDataset = (id) => setField("datasets", (state.datasets || []).filter((d) => d.id !== id));
  const updateDataset = (id, patch) => setField("datasets", (state.datasets || []).map((d) => (d.id === id ? { ...d, ...patch } : d)));
  const toggleDataset = (id) => setCollapsedDatasets((prev) => ({ ...prev, [id]: !prev[id] }));

  const numeric = state.numericColumns || [];
  const selectedSet = new Set(state.columns || []);
  const canRun = (state.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim()) && (state.columns || []).length > 0 && !loading;

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Clustering Settings</h3>
        <p className="hint">Interactive embedding preview with optional KMeans coloring.</p>
      </div>
      <div className="seg-scroll">
        <div className="dataset-list">
            {(state.datasets || []).map((d, idx) => (
              <div className="dataset" key={d.id}>
                <div className="row dataset-header-row">
                  <DatasetCollapseButton collapsed={!!collapsedDatasets[d.id]} onClick={() => toggleDataset(d.id)} label={d.name || `Dataset ${idx + 1}`} />
                  <div className="dataset-title">{d.name?.trim() || `Dataset ${idx + 1}`}</div>
                  {(state.datasets || []).length > 1 && (
                    <button className="ghost btn-small" title="Remove this dataset from the clustering configuration." onClick={() => {
                      if (confirmRemoveFilled(d, `Dataset ${idx + 1}`)) removeDataset(d.id);
                    }}>Remove</button>
                  )}
                  <DatasetBadge>#{idx + 1}</DatasetBadge>
                </div>
                {!collapsedDatasets[d.id] && (
                  <>
                    <div className="row">
                      <label className="checkbox" style={{ minWidth: 62 }}>
                        <input
                          type="checkbox"
                          checked={d.enabled !== false}
                          onChange={(e) => updateDataset(d.id, { enabled: e.target.checked })}
                        />
                        use
                      </label>
                      <div style={{ flex: 1 }}>
                        <div className="field-head">Dataset name <Tip text="Friendly label used to identify this dataset in the embedding preview." /></div>
                        <input
                          className="input"
                          value={d.name || ""}
                          onChange={(e) => updateDataset(d.id, { name: e.target.value })}
                          placeholder={`Dataset ${idx + 1} name`}
                        />
                      </div>
                    </div>
                    <div className="row path-row">
                      <div style={{ flex: 1 }}>
                        <div className="field-head">CSV path <Tip text="Local CSV file used to compute the embedding." /></div>
                        <input className="input" value={d.path || ""} onChange={(e) => updateDataset(d.id, { path: e.target.value })} placeholder="/path/Results.csv" />
                      </div>
                      <button
                        className="secondary"
                        title="Choose a CSV file for this clustering dataset."
                        onClick={async () => {
                          try {
                            const picked = await onPickCsv();
                            if (picked) updateDataset(d.id, { path: picked, name: (d.name || "").trim() ? d.name : String(picked).split("/").pop() || d.name });
                          } catch {
                            // no-op
                          }
                        }}
                      >
                        <BrowseLabel>Browse CSV</BrowseLabel>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
            <button className="secondary add-dataset-button" title="Add another CSV dataset to the clustering configuration." onClick={addDataset}>Add dataset</button>
        </div>

        <details open className="seg-section">
          <summary>Features</summary>
          <div className="seg-body">
            <div className="field-head">Numeric features <Tip text="Numeric columns used as input features for UMAP or PCA." /></div>
            <select
              className="input"
              multiple
              size={Math.min(10, Math.max(4, numeric.length || 4))}
              value={state.columns || []}
              onChange={(e) => {
                const vals = Array.from(e.target.selectedOptions).map((o) => o.value);
                setField("columns", vals);
              }}
            >
              {numeric.map((c) => <option key={`umap-col-${c}`} value={c}>{c}</option>)}
            </select>
            <div className="row row-right">
              <button className="ghost btn-small" title="Select all numeric columns as embedding features." onClick={() => setField("columns", numeric.slice())}>Select all</button>
              <button className="ghost btn-small" title="Clear the selected embedding features." onClick={() => setField("columns", [])}>Clear</button>
            </div>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Embedding options</summary>
          <div className="seg-body">
            <div className="field-head">Embedding method <Tip text="Choose whether to compute a UMAP embedding or a PCA projection." /></div>
            <select className="input" value={state.method || "umap"} onChange={(e) => setField("method", e.target.value)}>
              <option value="umap">UMAP</option>
              <option value="pca">PCA</option>
            </select>
            {state.method !== "pca" && (
              <>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Neighbors <Tip text="Number of nearest neighbors used by UMAP to preserve local structure." /></div>
                <input className="input" type="number" min="2" value={state.n_neighbors ?? 15} onChange={(e) => setField("n_neighbors", Number(e.target.value || 15))} placeholder="n_neighbors" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Minimum distance <Tip text="How tightly UMAP is allowed to pack points in the embedding." /></div>
                <input className="input" type="number" min="0" max="0.99" step="0.01" value={state.min_dist ?? 0.1} onChange={(e) => setField("min_dist", Number(e.target.value || 0.1))} placeholder="min_dist" />
              </div>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Metric <Tip text="Distance metric used to compare rows before embedding." /></div>
                <select className="input" value={state.metric || "euclidean"} onChange={(e) => setField("metric", e.target.value)}>
                {["euclidean", "manhattan", "cosine", "chebyshev", "canberra", "correlation"].map((m) => (
                  <option key={`metric-${m}`} value={m}>{m}</option>
                ))}
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Max points <Tip text="Maximum number of rows sampled into the preview to keep interaction responsive." /></div>
                <input className="input" type="number" min="500" step="500" value={state.max_points ?? 12000} onChange={(e) => setField("max_points", Number(e.target.value || 12000))} placeholder="max points" />
              </div>
            </div>
              </>
            )}
            {state.method === "pca" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Max points <Tip text="Maximum number of rows sampled into the PCA preview." /></div>
                  <input className="input" type="number" min="500" step="500" value={state.max_points ?? 12000} onChange={(e) => setField("max_points", Number(e.target.value || 12000))} placeholder="max points" />
                </div>
              </div>
            )}
            <label className="checkbox">
              <input type="checkbox" checked={!!state.scale} onChange={(e) => setField("scale", e.target.checked)} />
              Standardize features (z-score) <Tip text="Normalize features before embedding so large-scale variables do not dominate." />
            </label>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Coloring</summary>
          <div className="seg-body">
            <label className="checkbox">
              <input type="checkbox" checked={!!state.use_clusters} onChange={(e) => setField("use_clusters", e.target.checked)} />
              Use KMeans clusters <Tip text="Color the embedding by KMeans cluster assignment instead of a metadata column." />
            </label>
            {state.use_clusters ? (
              <>
                <div className="field-head">Number of clusters (k)</div>
                <input className="input" type="number" min="2" value={state.n_clusters ?? 8} onChange={(e) => setField("n_clusters", Number(e.target.value || 8))} placeholder="k for KMeans coloring" />
                <div className="field-head">Elbow range</div>
                <div className="row">
                  <input className="input" type="number" min="2" value={state.k_min ?? 2} onChange={(e) => setField("k_min", Number(e.target.value || 2))} placeholder="Minimum k" />
                  <input className="input" type="number" min="3" value={state.k_max ?? 12} onChange={(e) => setField("k_max", Number(e.target.value || 12))} placeholder="Maximum k" />
                </div>
                <button className="ghost" title="Generate an elbow plot across the selected k range to help choose the number of clusters." onClick={onElbow} disabled={loading || elbowLoading}>
                  {elbowLoading ? "Generating elbow..." : "Generate elbow plot"}
                </button>
              </>
            ) : (
              <>
              <div className="field-head">Color by <Tip text="Column used to color the embedding when KMeans coloring is disabled." /></div>
              <select className="input" value={state.color_by || ""} onChange={(e) => setField("color_by", e.target.value)}>
                <option value="">Color by default (Condition)</option>
                {(state.columnsAll || []).map((c) => <option key={`color-${c}`} value={c}>{c}</option>)}
              </select>
              </>
            )}
          </div>
        </details>
      </div>

      <div className="seg-footer">
        <button className="primary" title="Compute the embedding preview with the selected datasets, features, and coloring options." onClick={onPreview} disabled={!canRun}>
          {loading ? "Running..." : "Run"}
        </button>
      </div>
      <Status level={status.level} text={status.text} />
    </Card>
  );
}

function StatsLeftPanel({ onPickCsv, onRun, status, loading, state, setState }) {
  const [collapsedDatasets, setCollapsedDatasets] = React.useState({});
  const setField = (k, v) => setState((prev) => ({ ...prev, [k]: v }));
  const addDataset = () => setField("datasets", [...(state.datasets || []), { id: makeRowId(), name: `Dataset ${(state.datasets || []).length + 1}`, path: "", enabled: true }]);
  const removeDataset = (id) => setField("datasets", (state.datasets || []).filter((d) => d.id !== id));
  const updateDataset = (id, patch) => setField("datasets", (state.datasets || []).map((d) => (d.id === id ? { ...d, ...patch } : d)));
  const toggleDataset = (id) => setCollapsedDatasets((prev) => ({ ...prev, [id]: !prev[id] }));
  const addFilter = () => setField("filters", [...(state.filters || []), makeStatsFilterRow()]);
  const removeFilter = (id) => setField("filters", (state.filters || []).filter((f) => f.id !== id));
  const updateFilter = (id, patch) => setField("filters", (state.filters || []).map((f) => (f.id === id ? { ...f, ...patch } : f)));
  const cols = state.columns || [];
  const categoricalCols = state.categoricalColumns || [];
  const method = state.method || "oneway";
  const canRun = (state.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim()) && !loading;
  const methodHelp = {
    oneway: "Compares one numeric variable across multiple groups (e.g., Control vs Treatments).",
    twoway: "Evaluates two factors simultaneously and their possible interaction effect.",
    chi2: "Tests association between two categorical variables using a contingency table.",
    "chi2-subgroups": "Compares conditions within each categorical subgroup (2x2 tests per subgroup).",
  };

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Statistics Settings</h3>
        <p className="hint">Run statistical tests and inspect result tables.</p>
      </div>
      <div className="seg-scroll">
        <div className="dataset-list">
            {(state.datasets || []).map((d, idx) => (
              <div className="dataset" key={d.id}>
                <div className="row dataset-header-row">
                  <DatasetCollapseButton collapsed={!!collapsedDatasets[d.id]} onClick={() => toggleDataset(d.id)} label={d.name || `Dataset ${idx + 1}`} />
                  <div className="dataset-title">{d.name?.trim() || `Dataset ${idx + 1}`}</div>
                  {(state.datasets || []).length > 1 && (
                    <button className="ghost btn-small" onClick={() => {
                      if (confirmRemoveFilled(d, `Dataset ${idx + 1}`)) removeDataset(d.id);
                    }}>Remove</button>
                  )}
                  <DatasetBadge>#{idx + 1}</DatasetBadge>
                </div>
                {!collapsedDatasets[d.id] && (
                  <>
                    <div className="row">
                      <label className="checkbox" style={{ minWidth: 62 }}>
                        <input
                          type="checkbox"
                          checked={d.enabled !== false}
                          onChange={(e) => updateDataset(d.id, { enabled: e.target.checked })}
                        />
                        use
                      </label>
                      <div style={{ flex: 1 }}>
                        <div className="field-head">Dataset name <Tip text="Friendly name used to identify this file in the analysis." /></div>
                        <input
                          className="input"
                          value={d.name || ""}
                          onChange={(e) => updateDataset(d.id, { name: e.target.value })}
                          placeholder={`Dataset ${idx + 1} name`}
                        />
                      </div>
                    </div>
                    <div className="row path-row">
                      <div style={{ flex: 1 }}>
                        <div className="field-head">CSV path <Tip text="Local path to the CSV file containing your data." /></div>
                        <input className="input" value={d.path || ""} onChange={(e) => updateDataset(d.id, { path: e.target.value })} placeholder="/path/Results.csv" />
                      </div>
                      <button
                        className="secondary"
                        onClick={async () => {
                          try {
                            const picked = await onPickCsv();
                            if (picked) updateDataset(d.id, { path: picked, name: (d.name || "").trim() ? d.name : String(picked).split("/").pop() || d.name });
                          } catch {
                            // noop
                          }
                        }}
                      >
                        <BrowseLabel>Browse CSV</BrowseLabel>
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
            <button className="secondary add-dataset-button" onClick={addDataset}>Add dataset</button>
        </div>

        <details open className="seg-section">
          <summary>Test</summary>
          <div className="seg-body">
            <div className="field-head">Test method <Tip text="Choose the statistical test you want to run." /></div>
            <select className="input" value={method} onChange={(e) => setField("method", e.target.value)}>
              <option value="oneway">One-way</option>
              <option value="twoway">Two-way</option>
              <option value="chi2">Chi-square</option>
              <option value="chi2-subgroups">Chi-square subgroups</option>
            </select>
            <div className="hint">{methodHelp[method]}</div>

            {(method === "oneway" || method === "twoway") && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Numeric column <Tip text="Numeric variable to compare across groups." /></div>
                <select className="input" value={state.numeric_col || ""} onChange={(e) => setField("numeric_col", e.target.value)}>
                  <option value="">Numeric column</option>
                  {cols.map((c) => <option key={`sn-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {method === "oneway" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Group column <Tip text="Categorical column that defines the groups to compare." /></div>
                <select className="input" value={state.group_col || ""} onChange={(e) => setField("group_col", e.target.value)}>
                  <option value="">Group column</option>
                  {cols.map((c) => <option key={`sg-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {method === "twoway" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Factor A <Tip text="First categorical factor in the two-way analysis." /></div>
                <select className="input" value={state.group_col1 || ""} onChange={(e) => setField("group_col1", e.target.value)}>
                  <option value="">Factor A</option>
                  {cols.map((c) => <option key={`sga-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Factor B <Tip text="Second categorical factor in the two-way analysis." /></div>
                <select className="input" value={state.group_col2 || ""} onChange={(e) => setField("group_col2", e.target.value)}>
                  <option value="">Factor B</option>
                  {cols.map((c) => <option key={`sgb-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {method === "chi2" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Group column <Tip text="Row groups in the contingency table." /></div>
                <select className="input" value={state.group_col || ""} onChange={(e) => setField("group_col", e.target.value)}>
                  <option value="">Group column</option>
                  {cols.map((c) => <option key={`scg-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Category column <Tip text="Category levels represented as columns in the contingency table." /></div>
                <select className="input" value={state.category_col || ""} onChange={(e) => setField("category_col", e.target.value)}>
                  <option value="">Category column</option>
                  {cols.map((c) => <option key={`scc-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {method === "chi2-subgroups" && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Subgroup column <Tip text="Base category used to split subgroup comparisons." /></div>
                <select className="input" value={state.group_col || ""} onChange={(e) => setField("group_col", e.target.value)}>
                  <option value="">Group column</option>
                  {cols.map((c) => <option key={`ssg-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Condition column <Tip text="Conditions that will be compared within each subgroup." /></div>
                <select className="input" value={state.condition_col || ""} onChange={(e) => setField("condition_col", e.target.value)}>
                  <option value="">Condition column</option>
                  {cols.map((c) => <option key={`ssc-${c}`} value={c}>{c}</option>)}
                </select>
                </div>
              </div>
            )}

            {(method === "oneway" || method === "twoway") && (
              <div>
                <div className="field-head">Alpha <Tip text="Significance threshold. Default: 0.05." /></div>
                <input className="input" type="number" step="0.001" min="0" max="1" value={state.alpha ?? 0.05} onChange={(e) => setField("alpha", Number(e.target.value || 0.05))} placeholder="alpha" />
              </div>
            )}

            {(method === "chi2" || method === "chi2-subgroups") && (
              <div className="row">
                <div style={{ flex: 1 }}>
                  <div className="field-head">Expected minimum <Tip text="Minimum expected count threshold used to trigger fallback methods (e.g., Fisher/Monte Carlo)." /></div>
                  <input className="input" type="number" step="0.1" min="0" value={state.expected_min ?? 5.0} onChange={(e) => setField("expected_min", Number(e.target.value || 5.0))} placeholder="expected min" />
                </div>
                <div style={{ flex: 1 }}>
                  <div className="field-head">Correction method <Tip text="Multiple-comparison correction used in post-hoc results." /></div>
                <select className="input" value={state.correction_method || "auto"} onChange={(e) => setField("correction_method", e.target.value)}>
                  <option value="auto">Correction: auto</option>
                  <option value="bonferroni">Correction: bonferroni</option>
                  <option value="fdr_bh">Correction: fdr_bh</option>
                </select>
                </div>
              </div>
            )}

            {(method === "oneway" || method === "twoway") && (
              <div>
                <div className="field-head">Pairs of interest (optional) <Tip text="Specific pairs for post-hoc testing. Example: A|B; A|C." /></div>
                <input className="input" value={state.pairs_text || ""} onChange={(e) => setField("pairs_text", e.target.value)} placeholder="Pairs (optional): A|B; A|C" />
              </div>
            )}
          </div>
        </details>

        <details open className="seg-section">
          <summary>Subset data</summary>
          <div className="seg-body">
            <div className="hint">Optional exact-match filters applied before the test. Example: `Condition = control` and `Frame = 1`.</div>
            {(state.filters || []).map((filter, idx) => {
              const valueOptions = state.filterValueOptions?.[filter.column] || [];
              return (
                <div className="dataset" key={filter.id}>
                  <div className="row">
                    <DatasetBadge>Filter #{idx + 1}</DatasetBadge>
                    <div style={{ flex: 1 }}>
                      <div className="field-head">Filter column <Tip text="Column used to subset rows before running the analysis." /></div>
                      <select
                        className="input"
                        value={filter.column || ""}
                        onChange={(e) => updateFilter(filter.id, { column: e.target.value, values: [] })}
                      >
                        <option value="">No filter</option>
                        {cols.map((c) => <option key={`sf-col-${filter.id}-${c}`} value={c}>{c}</option>)}
                      </select>
                    </div>
                    {(state.filters || []).length > 1 && (
                      <button className="ghost btn-small" onClick={() => {
                        if (confirmRemoveFilled(filter, `Filter ${idx + 1}`)) removeFilter(filter.id);
                      }}>Remove</button>
                    )}
                  </div>
                  {filter.column ? (
                    <div>
                      <div className="field-head">Accepted values <Tip text="Only rows matching one of the selected values will be kept." /></div>
                      <select
                        className="input"
                        multiple
                        size={Math.min(6, Math.max(3, valueOptions.length || 3))}
                        value={filter.values || []}
                        onChange={(e) => updateFilter(filter.id, {
                          values: Array.from(e.target.selectedOptions || []).map((opt) => opt.value),
                        })}
                      >
                        {valueOptions.map((value) => <option key={`sf-val-${filter.id}-${value}`} value={value}>{value}</option>)}
                      </select>
                      <div className="hint">
                        {valueOptions.length
                          ? "Use Ctrl/Cmd-click to select more than one value."
                          : "No values loaded yet for this column."}
                      </div>
                    </div>
                  ) : null}
                </div>
              );
            })}
            <button className="secondary" onClick={addFilter}>Add filter</button>
            {categoricalCols.length > 0 && (
              <div className="hint">Suggested categorical columns: {categoricalCols.join(", ")}</div>
            )}
          </div>
        </details>
      </div>
      <div className="seg-footer">
        <button className="primary" onClick={onRun} disabled={!canRun}>
          {loading ? "Running..." : "Run"}
        </button>
      </div>
      <Status level={status.level} text={status.text} />
    </Card>
  );
}

function GatingLeftPanel({ onPickCsv, onPickDirectory, onPreview, onApply, onAxesChanged, status, loading, applying, state, setState }) {
  const [collapsedDatasets, setCollapsedDatasets] = React.useState({});
  const setField = (k, v) => setState((prev) => ({ ...prev, [k]: v }));
  const setAxisField = (k, v) => setState((prev) => ({
    ...prev,
    [k]: v,
    x_min: "",
    x_max: "",
    y_min: "",
    y_max: "",
    figure: null,
    tables: [],
    files: [],
    message: "",
  }));
  const handleAxisChange = (k, v) => {
    setAxisField(k, v);
    onAxesChanged?.();
  };
  const addDataset = () => setField("datasets", [...(state.datasets || []), { id: makeRowId(), name: `Dataset ${(state.datasets || []).length + 1}`, path: "", pkl_dir: "", enabled: true }]);
  const removeDataset = (id) => setField("datasets", (state.datasets || []).filter((d) => d.id !== id));
  const updateDataset = (id, patch) => setField("datasets", (state.datasets || []).map((d) => (d.id === id ? { ...d, ...patch } : d)));
  const toggleDataset = (id) => setCollapsedDatasets((prev) => ({ ...prev, [id]: !prev[id] }));
  const numeric = state.numericColumns || [];
  const busy = !!loading || !!applying;
  const hasDatasets = (state.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim());
  const canPreview = hasDatasets && !!state.x_col && !!state.y_col && !busy;
  const hasMissingPkl = !!state.draw_images && (state.datasets || []).some((d) => d.enabled !== false && String(d.path || "").trim() && !String(d.pkl_dir || "").trim());
  const canApply = canPreview && !!String(state.output_dir || "").trim() && !hasMissingPkl;

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Gating Settings</h3>
        <p className="hint">Filter populations by rectangular gates on two numeric columns, including cleanup of segmentation errors/debris.</p>
      </div>
      <div className="seg-scroll">
        <div className="dataset-list">
            {(state.datasets || []).map((d, idx) => (
              <div className="dataset" key={d.id}>
                <div className="row dataset-header-row">
                  <DatasetCollapseButton collapsed={!!collapsedDatasets[d.id]} onClick={() => toggleDataset(d.id)} label={d.name || `Dataset ${idx + 1}`} />
                  <div className="dataset-title">{d.name?.trim() || `Dataset ${idx + 1}`}</div>
                  {(state.datasets || []).length > 1 && (
                    <button className="ghost btn-small" title="Remove this dataset from the gating analysis." onClick={() => {
                      if (confirmRemoveFilled(d, `Dataset ${idx + 1}`)) removeDataset(d.id);
                    }}>Remove</button>
                  )}
                  <DatasetBadge>#{idx + 1}</DatasetBadge>
                </div>
                {!collapsedDatasets[d.id] && (
                  <>
                    <div className="row">
                      <label className="checkbox" style={{ minWidth: 62 }}>
                        <input type="checkbox" checked={d.enabled !== false} onChange={(e) => updateDataset(d.id, { enabled: e.target.checked })} />
                        use
                      </label>
                      <div style={{ flex: 1 }}>
                        <div className="field-head">Dataset name <Tip text="Friendly label shown in the gating preview and saved outputs." /></div>
                        <input className="input" value={d.name || ""} onChange={(e) => updateDataset(d.id, { name: e.target.value })} placeholder={`Dataset ${idx + 1} name`} />
                      </div>
                    </div>
                    <div className="row path-row">
                      <div style={{ flex: 1 }}>
                        <div className="field-head">CSV path <Tip text="Local CSV file that will be filtered by the gate." /></div>
                        <input className="input" value={d.path || ""} onChange={(e) => updateDataset(d.id, { path: e.target.value })} placeholder="/path/Results.csv" />
                      </div>
                      <button
                        className="secondary"
                        title="Choose a CSV file for this gating dataset."
                        onClick={async () => {
                          try {
                            const picked = await onPickCsv();
                            if (picked) updateDataset(d.id, { path: picked, name: (d.name || "").trim() ? d.name : String(picked).split("/").pop() || d.name });
                          } catch {
                            // no-op
                          }
                        }}
                      >
                        <BrowseLabel>Browse CSV</BrowseLabel>
                      </button>
                    </div>
                    {state.draw_images && (
                      <div className="row path-row">
                        <div style={{ flex: 1 }}>
                          <div className="field-head">PKL folder <Tip text="Folder containing the segmentation `.pkl` files for this dataset. Needed only if you want to redraw filtered images after gating." /></div>
                          <input className="input" value={d.pkl_dir || ""} onChange={(e) => updateDataset(d.id, { pkl_dir: e.target.value })} placeholder="/path/pkl-data" />
                        </div>
                        <button
                          className="secondary"
                          title="Choose the PKL folder associated with this dataset."
                          onClick={async () => {
                            try {
                              const picked = await onPickDirectory();
                              if (picked) updateDataset(d.id, { pkl_dir: picked });
                            } catch {
                              // no-op
                            }
                          }}
                        >
                          <BrowseLabel>Browse PKL</BrowseLabel>
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
            <button className="secondary add-dataset-button" title="Add another CSV dataset to the gating analysis." onClick={addDataset}>Add dataset</button>
        </div>

        <details open className="seg-section">
          <summary>Gate setup</summary>
          <div className="seg-body">
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">X column <Tip text="Numeric column plotted on the horizontal axis of the gate." /></div>
                <select className="input" value={state.x_col || ""} onChange={(e) => handleAxisChange("x_col", e.target.value)}>
                <option value="">X column</option>
                {numeric.map((c) => <option key={`gx-${c}`} value={c}>{c}</option>)}
                </select>
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Y column <Tip text="Numeric column plotted on the vertical axis of the gate." /></div>
                <select className="input" value={state.y_col || ""} onChange={(e) => handleAxisChange("y_col", e.target.value)}>
                <option value="">Y column</option>
                {numeric.map((c) => <option key={`gy-${c}`} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Low quantile <Tip text="Lower quantile used to estimate automatic bounds when explicit limits are empty." /></div>
                <input className="input" type="number" min="0" max="0.49" step="0.01" value={state.q_low ?? 0.05} onChange={(e) => setField("q_low", Number(e.target.value || 0.05))} placeholder="Low quantile" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">High quantile <Tip text="Upper quantile used to estimate automatic bounds when explicit limits are empty." /></div>
                <input className="input" type="number" min="0.51" max="1" step="0.01" value={state.q_high ?? 0.95} onChange={(e) => setField("q_high", Number(e.target.value || 0.95))} placeholder="High quantile" />
              </div>
            </div>
            <div className="hint">If bounds are empty, they are estimated from quantiles (legacy filters behavior).</div>
          </div>
        </details>

        <details open className="seg-section">
          <summary>Output</summary>
          <div className="seg-body">
            <label className="checkbox">
              <input type="checkbox" checked={!!state.draw_images} onChange={(e) => setField("draw_images", e.target.checked)} />
              Apply gate to images too <Tip text="When enabled, the gate is also applied to segmentation PKL files so the software redraws filtered images, in addition to saving gated CSV files." />
            </label>
            {state.draw_images && (
              <div className="hint">Provide one PKL folder for each dataset above. The software will redraw images using only the nuclei kept by the gate.</div>
            )}
            <div className="field-head">Saving path <Tip text="Directory where gated CSV files, logs, and optional redrawn image outputs will be written." /></div>
            <div className="row path-row">
              <input className="input" value={state.output_dir || ""} onChange={(e) => setField("output_dir", e.target.value)} placeholder="Folder to save gating outputs" />
              <button
                className="secondary"
                title="Choose where gated CSV files should be saved."
                onClick={async () => {
                  try {
                    const picked = await onPickDirectory();
                    if (picked) setField("output_dir", picked);
                  } catch {
                    // no-op
                  }
                }}
              >
                <BrowseLabel>Browse</BrowseLabel>
              </button>
            </div>
            {hasMissingPkl && (
              <div className="hint" style={{ color: "var(--danger)" }}>
                Add a PKL folder for every active dataset before applying the gate to images.
              </div>
            )}
          </div>
        </details>
      </div>
      <div className="seg-footer">
        <button className="secondary" title="Preview the gate on the selected X/Y columns without saving files yet." onClick={onPreview} disabled={!canPreview}>
          {loading ? "Previewing..." : "Preview gate"}
        </button>
        <button className="primary" title="Apply the gate and save the filtered CSV files to the selected output folder." onClick={onApply} disabled={!canApply}>
          {applying ? "Applying..." : "Apply and save"}
        </button>
      </div>
      <Status level={status.level} text={status.text} />
    </Card>
  );
}

function TrackingLeftPanel({
  onPickCsv,
  onPickDirectory,
  onRunAutomatic,
  onGoToCorrection,
  onOpenCorrection,
  onSaveResults,
  onRefreshFrame,
  onPrevFrame,
  onNextFrame,
  onDeleteTracks,
  onLinkTracks,
  status,
  state,
  setState,
  running,
  loadingFrame,
  editing,
}) {
  const setField = (k, v) => setState((prev) => ({ ...prev, [k]: v }));
  const busy = running || loadingFrame || editing;
  const hasTracked = !!String(state.table_path || "").trim();
  const imageNameColumns = (state.columns || []).filter((c) => String(c || "").toLowerCase().includes("image_name"));
  const workflowStage = String(state.workflow_stage || "step1");
  const hasSelection = (state.selected || []).length > 0;
  const canRun = !!String(state.path_to_table || "").trim()
    && !!String(state.image_dir || "").trim()
    && !!String(state.image_col || "").trim()
    && !busy;
  const canGoToCorrection = hasTracked && !busy;
  const canSaveResults = hasTracked && !!String(state.save_results_dir || "").trim() && !busy;
  const canPreview = hasTracked && !busy;
  const canDelete = hasTracked && hasSelection && !busy;
  const canLink = hasTracked && (state.selected || []).length >= 2 && !busy;

  return (
    <Card as="aside" className="panel seg-panel" variant="panel">
      <div className="seg-header">
        <h3>Tracking Settings</h3>
        <p className="hint">
          Automatic tracking is simple and may produce errors. Step 2 is manual correction and becomes available only
          after running automatic tracking.
        </p>
      </div>
      <div className="seg-scroll">
        {workflowStage === "step1" && (
          <details open className="seg-section">
          <summary>Step 1 - Automatic tracking</summary>
          <div className="seg-body">
            <div className="field-head">Tracking table</div>
            <div className="row path-row">
              <input className="input" value={state.path_to_table || ""} onChange={(e) => setField("path_to_table", e.target.value)} placeholder="/path/Results.csv" />
              <button
                className="secondary"
                title="Open a file picker to choose the tracking Results.csv input table."
                onClick={async () => {
                  try {
                    const p = await onPickCsv();
                    if (p) setField("path_to_table", p);
                  } catch {
                    // no-op
                  }
                }}
              >
                <BrowseLabel>Browse CSV</BrowseLabel>
              </button>
            </div>
            <div className="field-head">Image folder</div>
            <div className="row path-row">
              <input className="input" value={state.image_dir || ""} onChange={(e) => setField("image_dir", e.target.value)} placeholder="Image folder (required)" />
              <button
                className="secondary"
                title="Choose the folder containing the source images used by the tracking viewer."
                onClick={async () => {
                  try {
                    const p = await onPickDirectory();
                    if (p) setField("image_dir", p);
                  } catch {
                    // no-op
                  }
                }}
              >
                <BrowseLabel>Browse</BrowseLabel>
              </button>
            </div>
            <div className="hint">This folder is used to render the tracking viewer images.</div>
            <div className="field-head">
              Image name column <Tip text="Required. Choose the CSV column that stores image file names. These names must exactly match files inside the selected image folder." />
            </div>
            <select
              className="input"
              value={state.image_col || ""}
              onChange={(e) => setField("image_col", e.target.value)}
            >
              <option value="">Select image column</option>
              {imageNameColumns.map((col) => (
                <option key={`tracking-img-col-${col}`} value={col}>{col}</option>
              ))}
            </select>
            <div className="hint">The values in this column must match the image filenames in the folder above.</div>
            <div className="field-head">Tracking parameters</div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Max distance <Tip text="Maximum distance allowed to link a cell to a candidate in the next frame." /></div>
                <input className="input" type="number" min="1" value={state.max_distance ?? 30} onChange={(e) => setField("max_distance", Number(e.target.value || 30))} placeholder="max distance" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Time window <Tip text="How many frames the tracker can remember when reconnecting interrupted trajectories." /></div>
                <input className="input" type="number" min="1" value={state.time_window ?? 5} onChange={(e) => setField("time_window", Number(e.target.value || 5))} placeholder="time window" />
              </div>
            </div>
            <div className="row">
              <div style={{ flex: 1 }}>
                <div className="field-head">Max split distance <Tip text="Maximum distance used to detect possible split events between nearby trajectory segments." /></div>
                <input className="input" type="number" min="1" value={state.max_split_distance ?? 10} onChange={(e) => setField("max_split_distance", Number(e.target.value || 10))} placeholder="max split distance" />
              </div>
              <div style={{ flex: 1 }}>
                <div className="field-head">Gap closing distance <Tip text="Maximum distance allowed when reconnecting a trajectory after a temporary gap." /></div>
                <input className="input" type="number" min="1" value={state.max_gap_closing_distance ?? 30} onChange={(e) => setField("max_gap_closing_distance", Number(e.target.value || 30))} placeholder="max gap closing distance" />
              </div>
            </div>
            <div className="row">
              <button className="primary" title="Run automatic tracking with the parameters above and generate the first tracked table." onClick={onRunAutomatic} disabled={!canRun}>
                {running ? "Running..." : "Run tracking"}
              </button>
              <button className="secondary" title="Move to step 2 after a tracked table has been generated." onClick={onGoToCorrection} disabled={!canGoToCorrection}>
                Next
              </button>
            </div>
            <Status level={status.level} text={status.text} />
          </div>
          </details>
        )}

        {workflowStage === "menu" && (
          <details open className="seg-section">
            <summary>Step 2 - Choose action</summary>
            <div className="seg-body">
              <div className="field-head">1. Save results</div>
              <div className="row path-row">
                <input className="input" value={state.save_results_dir || ""} onChange={(e) => setField("save_results_dir", e.target.value)} placeholder="Folder to save table and tracking images" />
                <button
                  className="secondary"
                  title="Choose where the final table and rendered tracking images should be exported."
                  onClick={async () => {
                    try {
                      const p = await onPickDirectory();
                      if (p) setField("save_results_dir", p);
                    } catch {
                      // no-op
                    }
                  }}
                >
                  <BrowseLabel>Browse</BrowseLabel>
                </button>
              </div>
              <button className="secondary" title="Export the current tracked table and the cached tracking images to the selected folder." onClick={onSaveResults} disabled={!canSaveResults}>
                Save results
              </button>
              <div className="field-head" style={{ marginTop: 10 }}>2. Correct tracks</div>
              <button className="primary" title="Open the manual correction viewer to inspect and edit tracks." onClick={onOpenCorrection} disabled={!hasTracked || busy}>
                Correct tracks
              </button>
              <Status level={status.level} text={status.text} />
            </div>
          </details>
        )}

        {workflowStage === "correction" && (
          <details open className="seg-section">
            <summary>Step 2 - Manual correction</summary>
            <div className="seg-body">
              <div className="row row-right">
                <button className="ghost btn-small" title="Return to the step 2 menu without losing the current tracked table." onClick={onGoToCorrection} disabled={busy}>Back to options</button>
              </div>
              <div className="row path-row">
                <input className="input" value={state.image_dir || ""} onChange={(e) => setField("image_dir", e.target.value)} placeholder="Image folder for viewer" />
                <button
                  className="secondary"
                  title="Choose the image folder used by the correction viewer."
                  onClick={async () => {
                    try {
                      const p = await onPickDirectory();
                      if (p) setField("image_dir", p);
                    } catch {
                      // no-op
                    }
                  }}
                >
                  <BrowseLabel>Browse</BrowseLabel>
                </button>
              </div>
              <div className="hint">{state.preview_cache_dir ? "Viewer cache ready." : "Viewer cache will be generated automatically."}</div>
              <label className="checkbox">
                <input type="checkbox" checked={!!state.show_complete_trail} onChange={(e) => setField("show_complete_trail", e.target.checked)} />
                Show complete trail
              </label>
              <button className="secondary" title="Redraw the current frame using the latest table state and viewer settings." onClick={onRefreshFrame} disabled={!canPreview}>
                {loadingFrame ? "Updating..." : "Refresh preview"}
              </button>
              <button className="primary" title="Finish correction and open the final export options for the tracked table and images." onClick={() => setField("finish_open", !state.finish_open)} disabled={!hasTracked || busy}>
                {state.finish_open ? "Hide finish options" : "Finish"}
              </button>
              {state.finish_open && (
                <>
                  <div className="field-head">Finish output folder</div>
                  <div className="row path-row">
                    <input className="input" value={state.save_results_dir || ""} onChange={(e) => setField("save_results_dir", e.target.value)} placeholder="Folder to save final tracking outputs" />
                    <button
                      className="secondary"
                      title="Choose the folder where the final tracking outputs will be exported."
                      onClick={async () => {
                        try {
                          const p = await onPickDirectory();
                          if (p) setField("save_results_dir", p);
                        } catch {
                          // no-op
                        }
                      }}
                    >
                      <BrowseLabel>Browse</BrowseLabel>
                    </button>
                  </div>
                  <div className="row">
                    <button className="secondary" title="Export only the final tracked table to the selected folder." onClick={() => onSaveResults(false)} disabled={!canSaveResults}>
                      Save table only
                    </button>
                    <button className="primary" title="Export the final tracked table together with the rendered tracking images." onClick={() => onSaveResults(true)} disabled={!canSaveResults}>
                      Save table + images
                    </button>
                  </div>
                </>
              )}
              <Status level={status.level} text={status.text} />
            </div>
          </details>
        )}
      </div>
    </Card>
  );
}

function StatsTableView({ table, onDownload }) {
  const cols = table?.columns || [];
  const rows = table?.rows || [];
  const group1Key = cols.find((c) => ["group1", "grupo1"].includes(String(c).toLowerCase()));
  const group2Key = cols.find((c) => ["group2", "grupo2"].includes(String(c).toLowerCase()));
  const valueKey = cols.find((c) => ["p_tukey", "p_adjusted", "p_ajustado", "p_raw"].includes(String(c).toLowerCase()));
  const rejectKey = cols.find((c) => ["reject_h0", "significativo"].includes(String(c).toLowerCase()));
  const isPairwiseLongTable = !!group1Key && !!group2Key && !!valueKey && rows.length > 0;

  let displayCols = cols;
  let displayRows = rows;

  if (isPairwiseLongTable) {
    const labels = Array.from(
      new Set(
        rows.flatMap((row) => [String(row?.[group1Key] ?? ""), String(row?.[group2Key] ?? "")]).filter(Boolean)
      )
    );
    const pairMap = new Map();
    rows.forEach((row) => {
      const a = String(row?.[group1Key] ?? "");
      const b = String(row?.[group2Key] ?? "");
      const p = row?.[valueKey];
      const reject = rejectKey ? row?.[rejectKey] : null;
      const base = p == null || p === "" ? "" : String(p);
      const text = reject == null || reject === "" ? base : `${base}${String(reject) === "true" ? " *" : ""}`;
      if (!a || !b) return;
      pairMap.set(`${a}||${b}`, text);
      pairMap.set(`${b}||${a}`, text);
    });
    displayCols = ["group", ...labels];
    displayRows = labels.map((label) => {
      const out = { group: label };
      labels.forEach((other) => {
        out[other] = label === other ? "-" : (pairMap.get(`${label}||${other}`) || "");
      });
      return out;
    });
  }
  const rowHeaderKey = isPairwiseLongTable
    ? "group"
    : ((displayCols[0] === "" || String(displayCols[0] || "").toLowerCase() === "group") ? displayCols[0] : null);

  const handleCopy = async () => {
    if (!displayRows.length || !displayCols.length) return;
    const lines = [displayCols.map((c) => String(c ?? "")).join("\t")];
    displayRows.forEach((row) => {
      const vals = displayCols.map((c) => String(row?.[c] ?? ""));
      lines.push(vals.join("\t"));
    });
    await copyText(`${lines.join("\n")}\n`);
  };
  return (
    <div className="section table-section">
      <div className="row row-between">
        <h3>{table?.name || "Table"}</h3>
        <div className="row">
          <button className="ghost btn-small" onClick={handleCopy} disabled={!displayRows.length}>
            Copy table
          </button>
          <button className="ghost btn-small" onClick={() => onDownload?.(table)} disabled={!rows.length}>
            Download CSV
          </button>
        </div>
      </div>
      {!displayRows.length ? (
        <p className="hint">No rows.</p>
      ) : (
        <div className="table-wrap">
          <table className="results-table">
            <thead>
              <tr>{displayCols.map((c) => <th key={`th-${table.name}-${c}`}>{c}</th>)}</tr>
            </thead>
            <tbody>
              {displayRows.slice(0, 2000).map((r, i) => (
                <tr key={`tr-${table.name}-${i}`}>
                  {displayCols.map((c) => (
                    c === rowHeaderKey
                      ? <th key={`td-${table.name}-${i}-${c}`} scope="row" className="results-table-rowhead">{r[c] == null ? "" : String(r[c])}</th>
                      : <td key={`td-${table.name}-${i}-${c}`}>{r[c] == null ? "" : String(r[c])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const emptyRow = () => ({
  id: makeRowId(),
  name: "",
  path: "",
  area_col: "Area",
  nii_col: "NII",
  is_control: false,
  columns: null,
  area_columns: [],
  nii_columns: [],
});
const initialNmaRows = () => ([{
  ...emptyRow(),
  name: "Control",
  is_control: true,
}]);

function buildDatasets(rows) {
  return rows
    .filter((r) => r.path.trim())
    .map((r) => ({
      name: r.name?.trim() || r.path.split("/").pop(),
      path: r.path.trim(),
      area_col: r.area_col?.trim() || "",
      nii_col: r.nii_col?.trim() || "",
      is_control: !!r.is_control,
    }));
}

function cleanTechnicalMessage(value) {
  return String(value || "")
    .replace(/\b(TypeError|ValueError|KeyError|RuntimeError|Exception):\s*/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

function extractQuotedValue(value) {
  const match = String(value || "").match(/['"]([^'"]+)['"]/);
  return match ? match[1] : "";
}

function extractFileName(value) {
  const match = String(value || "").match(/['"]?([^'"\s/\\]+\.(?:csv|pkl|pickle|tif|tiff|png|jpg|jpeg))['"]?/i);
  return match ? match[1] : "";
}

function humanizeErrorMessage(value, fallback = "The operation could not be completed. Check the selected inputs and try again.") {
  const raw = cleanTechnicalMessage(value);
  if (!raw) return fallback;
  const lower = raw.toLowerCase();

  if (lower.includes("no columns to parse from file") || lower.includes("emptydataerror")) {
    return "The selected CSV appears to be empty or does not contain a readable table. Choose a CSV with column headers and at least one data row.";
  }

  if (lower.includes("not supported between instances") || lower.includes("unsupported operand type")) {
    return "The selected data contains incompatible values, such as numbers mixed with empty cells or text. Check the chosen columns and remove blank or non-numeric values where numeric measurements are required.";
  }

  if (lower.includes("nonetype") || lower.includes("none type")) {
    return "A required value is missing. Check that every required file, folder, channel, condition, and column is selected before running.";
  }

  if (lower.includes("could not convert string to float") || lower.includes("unable to parse string")) {
    return "A numeric column contains text or symbols. Select a measurement column that contains only numbers, or clean the CSV and try again.";
  }

  if (lower.includes("file not found") || lower.includes("no such file or directory")) {
    return "One of the selected files or folders was not found. Check that the path still exists and select it again if it was moved, renamed, or deleted.";
  }

  if (lower.includes("permission denied")) {
    return "The software does not have permission to read or write in the selected location. Choose a folder you can access, or adjust the folder permissions.";
  }

  if (lower.includes("is not in list") || lower.includes("keyerror")) {
    const column = extractQuotedValue(raw);
    return column
      ? `The column "${column}" was not found in the selected data. Check the CSV headers and choose an existing column.`
      : "A required column was not found in the selected data. Check the CSV headers and choose columns that exist in the file.";
  }

  if (lower.includes("all csvs must have exactly the same columns")) {
    return "The selected CSV files do not have the same columns. Use files with the same column names in the same order, or analyze them separately.";
  }

  if (lower.includes("no data left after") || lower.includes("no valid rows")) {
    return "No rows were left after applying the selected filters or removing empty values. Relax the filters, choose different columns, or use a CSV with more valid data.";
  }

  if (lower.includes("dbscan found no core clusters") || lower.includes("all noise")) {
    return "The automatic clustering could not find a stable control group. Try increasing the neighborhood size, relaxing DBSCAN settings, or checking that the control CSV has enough comparable cells.";
  }

  if (lower.includes("failed to read csv") || lower.includes("error tokenizing data") || lower.includes("parsererror")) {
    const fileName = extractFileName(raw);
    return `The CSV${fileName ? ` "${fileName}"` : ""} could not be read as a table. Check that it is a valid CSV with consistent separators, column headers, and rows.`;
  }

  if (/traceback|stack trace|at\s+\w+\s*\(|\.jsx:\d+|\.py:\d+/i.test(raw)) {
    return fallback;
  }

  return raw;
}

function errorMessageFromException(error, fallback) {
  return humanizeErrorMessage(error?.message || error, fallback);
}

function friendlyApiError(text, fallback = "Request failed.") {
  const raw = String(text || "").trim();
  if (!raw) return fallback;
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed?.detail === "string") return humanizeErrorMessage(parsed.detail, fallback);
    if (Array.isArray(parsed?.detail)) {
      const message = parsed.detail
        .map((item) => {
          const loc = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(" > ") : "";
          const msg = item.msg || item.message || JSON.stringify(item);
          return loc ? `${loc}: ${msg}` : msg;
        })
        .join("\n");
      return humanizeErrorMessage(message, fallback);
    }
    if (typeof parsed?.message === "string") return humanizeErrorMessage(parsed.message, fallback);
    if (typeof parsed?.error === "string") return humanizeErrorMessage(parsed.error, fallback);
  } catch {
    // Plain-text responses are already user-readable.
  }
  return humanizeErrorMessage(raw, fallback);
}

async function errorFromResponse(res, fallback = "Request failed.") {
  const text = await res.text();
  return friendlyApiError(text || res.statusText, fallback);
}

function Status({ level = "info", text }) {
  if (!text) return null;
  const labels = {
    success: "Success",
    error: "Needs attention",
    warning: "Warning",
    info: "Status",
  };
  const icons = {
    success: "OK",
    error: "!",
    warning: "!",
    info: "i",
  };
  const statusLevel = labels[level] ? level : "info";
  const displayText = statusLevel === "error" ? humanizeErrorMessage(text) : text;
  return (
    <div className={`status ${statusLevel}`} role={statusLevel === "error" ? "alert" : "status"} aria-live="polite">
      <span className="status-icon" aria-hidden="true">{icons[statusLevel]}</span>
      <div className="status-body">
        <strong>{labels[statusLevel]}</strong>
        <span>{displayText}</span>
      </div>
    </div>
  );
}

const NMA_COMPARTMENT_TOKENS = new Set(["nuc", "nucleus", "nuclear", "nuclei", "cyto", "cytoplasm", "cytoplasmic", "cytoplasmatic"]);
const NMA_MEASURE_EXCLUDE_TOKENS = new Set(["foci", "focus", "total", "mean", "median", "min", "max", "image", "ring", "ellipse", "fraction", "perimeter", "ratio", "radius", "draw", "fitellipse"]);

function nmaColumnTokens(column) {
  return String(column || "").toLowerCase().split(/[^a-z0-9]+/).filter(Boolean);
}

function isNmaMeasureColumn(column, measure) {
  const wanted = String(measure || "").toLowerCase();
  const tokens = nmaColumnTokens(column);
  if (!tokens.includes(wanted)) return false;
  const otherTokens = tokens.filter((token) => token !== wanted);
  if (otherTokens.some((token) => NMA_MEASURE_EXCLUDE_TOKENS.has(token))) return false;
  return otherTokens.every((token) => NMA_COMPARTMENT_TOKENS.has(token));
}

function nmaMeasureCandidates(columns, measure, serverCandidates = []) {
  const cols = (columns || []).map((c) => String(c));
  const exact = cols.filter((c) => c.toLowerCase() === String(measure).toLowerCase());
  const detected = cols.filter((c) => !exact.includes(c) && isNmaMeasureColumn(c, measure));
  const merged = [...(serverCandidates || []), ...exact, ...detected].map((c) => String(c));
  return Array.from(new Set(merged)).filter((c) => cols.includes(c));
}

function pickNmaMeasureColumn(columns, measure, current, serverCandidates = []) {
  const cols = (columns || []).map((c) => String(c));
  if (current && cols.includes(current)) return current;
  const candidates = nmaMeasureCandidates(cols, measure, serverCandidates);
  if (candidates.length === 1) return candidates[0];
  const exact = cols.find((c) => c.toLowerCase() === String(measure).toLowerCase());
  if (exact && candidates.length <= 1) return exact;
  return "";
}

function PlotPanel({ figure, config, onRelayout, onClick }) {
  const hostRef = React.useRef(null);
  const ref = React.useRef(null);
  const [plotWidth, setPlotWidth] = React.useState(960);
  const defaultConfig = {
    displayModeBar: true,
    displaylogo: false,
    responsive: true,
    scrollZoom: true,
    toImageButtonOptions: {
      format: "png",
      filename: "fornma-plot",
      scale: 2,
    },
  };

  React.useEffect(() => {
    if (!hostRef.current || typeof ResizeObserver === "undefined") return undefined;
    const updateWidth = () => {
      const rect = hostRef.current?.getBoundingClientRect();
      if (!rect?.width) return;
      setPlotWidth(Math.max(640, Math.min(1120, Math.floor(rect.width))));
    };
    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(hostRef.current);
    return () => observer.disconnect();
  }, []);

  React.useEffect(() => {
    if (!ref.current || !figure) return;
    const layout = {
      ...(figure.layout || {}),
      autosize: false,
      width: plotWidth,
    };
    Plotly.react(ref.current, figure.data || [], layout, config || defaultConfig).then(() => {
      if (ref.current) Plotly.Plots.resize(ref.current);
    });
    if (ref.current?.on) {
      if (ref.current.removeAllListeners) {
        ref.current.removeAllListeners("plotly_relayout");
        ref.current.removeAllListeners("plotly_click");
      }
      if (onRelayout) {
        ref.current.on("plotly_relayout", onRelayout);
      }
      if (onClick) {
        ref.current.on("plotly_click", onClick);
      }
    }
  }, [figure, config, onRelayout, onClick, plotWidth]);

  return (
    <div className="plot-host" ref={hostRef}>
      <div className="plot" style={{ width: `${plotWidth}px` }} ref={ref} />
    </div>
  );
}

function ellipseTrace(xc, yc, rx, ry, n = 256) {
  const x = [];
  const y = [];
  for (let i = 0; i < n; i += 1) {
    const t = (i / n) * Math.PI * 2;
    x.push(xc + rx * Math.cos(t));
    y.push(yc + ry * Math.sin(t));
  }
  return {
    x,
    y,
    mode: "lines",
    line: { width: 2, color: "#3A6EA5" },
    name: "threshold",
    hoverinfo: "skip",
  };
}

function buildStep1Figure(sample, stats, graphLimits, sdNii, sdArea) {
  const data = [];
  if (sample?.x?.length && sample?.y?.length) {
    data.push({
      x: sample.x,
      y: sample.y,
      mode: "markers",
      type: "scattergl",
      marker: { size: 6, opacity: 0.68, color: "#3A6EA5" },
      name: "Controls (sample)",
    });
  }
  const rx = sdNii * (stats?.sd_x || 1);
  const ry = sdArea * (stats?.sd_y || 1);
  data.push(ellipseTrace(stats?.mu_x || 0, stats?.mu_y || 0, rx, ry));
  const layout = {
    autosize: false,
    width: 640,
    height: 640,
    margin: { l: 60, r: 10, t: 50, b: 60 },
    title: { text: "NMA · Elipse de controle", x: 0.5, xanchor: "center" },
    xaxis: { title: "NII", range: [graphLimits?.[2] ?? 0, graphLimits?.[3] ?? 1], fixedrange: true },
    yaxis: { title: "Area", range: [graphLimits?.[0] ?? 0, graphLimits?.[1] ?? 1], fixedrange: true },
  };
  return { data, layout };
}

function buildControlGateFigure(gate, stats, graphLimits) {
  const preview = gate?.preview || {};
  const xs = preview.x || [];
  const ys = preview.y || [];
  const keep = preview.keep || [];
  const keptX = [];
  const keptY = [];
  const removedX = [];
  const removedY = [];
  xs.forEach((x, idx) => {
    if (keep[idx]) {
      keptX.push(x);
      keptY.push(ys[idx]);
    } else {
      removedX.push(x);
      removedY.push(ys[idx]);
    }
  });
  const data = [];
  if (removedX.length) {
    data.push({
      x: removedX,
      y: removedY,
      mode: "markers",
      type: "scattergl",
      marker: { size: 5, opacity: 0.3, color: "#9AA6B2" },
      name: "Removed from control gate",
    });
  }
  if (keptX.length) {
    data.push({
      x: keptX,
      y: keptY,
      mode: "markers",
      type: "scattergl",
      marker: { size: 6, opacity: 0.72, color: "#2F855A" },
      name: "Kept as normal control",
    });
  }
  const bounds = gate?.bounds || {};
  const x0 = bounds.x_min ?? graphLimits?.[2] ?? 0;
  const x1 = bounds.x_max ?? graphLimits?.[3] ?? 1;
  const y0 = bounds.y_min ?? graphLimits?.[0] ?? 0;
  const y1 = bounds.y_max ?? graphLimits?.[1] ?? 1;
  const layout = {
    autosize: false,
    width: 640,
    height: 640,
    margin: { l: 60, r: 10, t: 50, b: 60 },
    title: { text: "NMA · Gate do controle", x: 0.5, xanchor: "center" },
    xaxis: { title: "NII", range: [graphLimits?.[2] ?? x0, graphLimits?.[3] ?? x1], fixedrange: true },
    yaxis: { title: "Area", range: [graphLimits?.[0] ?? y0, graphLimits?.[1] ?? y1], fixedrange: true },
    shapes: [
      {
        type: "rect",
        x0,
        x1,
        y0,
        y1,
        line: { color: "#2F855A", width: 2 },
        fillcolor: "rgba(47, 133, 90, 0.08)",
        editable: true,
      },
    ],
    annotations: stats
      ? [
          {
            text: `Gate: ${gate?.kept ?? 0}/${gate?.total ?? 0} cells`,
            x: stats.mu_x,
            y: y1,
            xref: "x",
            yref: "y",
            showarrow: false,
            yanchor: "bottom",
            font: { size: 12, color: "#1F2D3D" },
            bgcolor: "rgba(247, 249, 252, 0.94)",
            bordercolor: "rgba(217, 226, 236, 0.95)",
            borderwidth: 1,
            borderpad: 4,
          },
        ]
      : [],
  };
  return { data, layout };
}

function computeThresholds(stats, sdNii, sdArea) {
  if (!stats) {
    return {
      v_up: 0,
      v_mid: 0,
      v_down: 0,
      v_down2: 0,
      y_high: 0,
      y_low: 0,
    };
  }
  const v = stats.mu_x + 1.5 * (sdNii || 1) * (stats.sd_x || 1);
  const y_high = stats.mu_y + (sdArea || 1) * (stats.sd_y || 1);
  const y_low = stats.mu_y - (sdArea || 1) * (stats.sd_y || 1);
  return {
    v_up: v,
    v_mid: v,
    v_down: stats.mu_x,
    v_down2: v,
    y_high,
    y_low,
  };
}

function buildQuadrantAnnotations(graphLimits, thresholds, stats, sdArea, percentages) {
  const xMin = graphLimits[2];
  const xMax = graphLimits[3];
  const yMin = graphLimits[0];
  const yMax = graphLimits[1];
  const yHigh = stats.mu_y + (sdArea || 1) * (stats.sd_y || 1);
  const yLow = stats.mu_y - (sdArea || 1) * (stats.sd_y || 1);
  const mid = (a, b) => (a + b) / 2;
  const makeText = (label) => {
    const pct = percentages?.[label];
    if (!pct) return label;
    const lines = Object.entries(pct)
      .sort((a, b) => b[1] - a[1])
      .map(([name, value]) => `${name}: ${value.toFixed(1)}%`);
    return [label, ...lines].join("<br>");
  };
  return [
    { label: "SR", x: mid(xMin, thresholds.v_down), y: mid(yMin, yLow) },
    { label: "S", x: mid(thresholds.v_down, thresholds.v_down2), y: mid(yMin, yLow) },
    { label: "SI", x: mid(thresholds.v_down2, xMax), y: mid(yMin, yLow) },
    { label: "N", x: mid(xMin, thresholds.v_mid), y: mid(yLow, yHigh) },
    { label: "I", x: mid(thresholds.v_mid, xMax), y: mid(yLow, yHigh) },
    { label: "LR", x: mid(xMin, thresholds.v_up), y: mid(yHigh, yMax) },
    { label: "LI", x: mid(thresholds.v_up, xMax), y: mid(yHigh, yMax) },
  ].map((a) => ({
    text: makeText(a.label),
    x: a.x,
    y: a.y,
    xref: "x",
    yref: "y",
    xanchor: "center",
    yanchor: "middle",
    showarrow: false,
    captureevents: false,
    font: { size: 12, color: "#1F2D3D" },
    bgcolor: "rgba(247, 249, 252, 0.94)",
    bordercolor: "rgba(217, 226, 236, 0.95)",
    borderwidth: 1,
    borderpad: 4,
  }));
}

function computeQuadrantPercentages(traces, thresholds, stats, sdArea) {
  if (!traces || !stats) return null;
  const yHigh = stats.mu_y + (sdArea || 1) * (stats.sd_y || 1);
  const yLow = stats.mu_y - (sdArea || 1) * (stats.sd_y || 1);
  const out = { LR: {}, LI: {}, N: {}, I: {}, SR: {}, S: {}, SI: {} };
  const toNum = (v) => {
    if (v == null) return NaN;
    if (typeof v === "string") return Number(v.replace(",", "."));
    return Number(v);
  };
  const toArray = (v) => {
    if (!v) return [];
    if (Array.isArray(v)) return v;
    if (ArrayBuffer.isView(v)) return Array.from(v);
    if (typeof v === "object") {
      if (v.bdata && v.dtype && typeof window !== "undefined") {
        try {
          const bin = atob(v.bdata);
          const buf = new ArrayBuffer(bin.length);
          const bytes = new Uint8Array(buf);
          for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i);
          let arr = null;
          if (v.dtype === "f4") arr = new Float32Array(buf);
          if (v.dtype === "f8") arr = new Float64Array(buf);
          if (v.dtype === "i4") arr = new Int32Array(buf);
          if (v.dtype === "i2") arr = new Int16Array(buf);
          if (arr) return Array.from(arr);
        } catch (_) {
          return [];
        }
      }
      if (Array.isArray(v.data)) return v.data;
      if (Array.isArray(v.values)) return v.values;
      if (Array.isArray(v.array)) return v.array;
    }
    return [];
  };
  traces.forEach((t) => {
    const name = t.name || "dataset";
    const xs = toArray(t.x);
    const ys = toArray(t.y);
    let total = 0;
    const counts = { LR: 0, LI: 0, N: 0, I: 0, SR: 0, S: 0, SI: 0 };
    for (let i = 0; i < xs.length; i += 1) {
      const x = toNum(xs[i]);
      const y = toNum(ys[i]);
      if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
      total += 1;
      if (y >= yHigh) {
        if (x < thresholds.v_up) counts.LR += 1;
        else counts.LI += 1;
      } else if (y >= yLow) {
        if (x < thresholds.v_mid) counts.N += 1;
        else counts.I += 1;
      } else {
        if (x < thresholds.v_down) counts.SR += 1;
        else if (x < thresholds.v_down2) counts.S += 1;
        else counts.SI += 1;
      }
    }
    Object.keys(counts).forEach((k) => {
      out[k][name] = total === 0 ? 0 : (counts[k] / total) * 100;
    });
  });
  return out;
}

function buildStep2Figure(
  traces,
  stats,
  graphLimits,
  thresholds,
  sdNii,
  sdArea,
  withLabels = false,
  verticalColor = "#D000FF",
  horizontalColor = "#3A6EA5"
) {
  const data = [...(traces || [])];
  const rx = (sdNii || 1) * (stats.sd_x || 1);
  const ry = (sdArea || 1) * (stats.sd_y || 1);
  data.push(ellipseTrace(stats.mu_x, stats.mu_y, rx, ry));

  const y_high = stats.mu_y + (sdArea || 1) * (stats.sd_y || 1);
  const y_low = stats.mu_y - (sdArea || 1) * (stats.sd_y || 1);
  const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
  const y_top = graphLimits[1];
  const y_bottom = graphLimits[0];

  const shapes = [
    {
      type: "line",
      x0: graphLimits[2],
      x1: graphLimits[3],
      y0: y_high,
      y1: y_high,
      line: { color: horizontalColor, width: 2 },
      editable: false,
    },
    {
      type: "line",
      x0: graphLimits[2],
      x1: graphLimits[3],
      y0: y_low,
      y1: y_low,
      line: { color: horizontalColor, width: 2 },
      editable: false,
    },
    {
      type: "line",
      x0: thresholds.v_down,
      x1: thresholds.v_down,
      y0: y_bottom,
      y1: y_low,
      line: { color: verticalColor, width: 3, dash: "solid" },
      editable: true,
    },
    {
      type: "line",
      x0: thresholds.v_down2,
      x1: thresholds.v_down2,
      y0: y_bottom,
      y1: y_low,
      line: { color: verticalColor, width: 3, dash: "solid" },
      editable: true,
    },
    {
      type: "line",
      x0: thresholds.v_mid,
      x1: thresholds.v_mid,
      y0: y_low,
      y1: y_high,
      line: { color: verticalColor, width: 3, dash: "solid" },
      editable: true,
    },
    {
      type: "line",
      x0: thresholds.v_up,
      x1: thresholds.v_up,
      y0: y_high,
      y1: y_top,
      line: { color: verticalColor, width: 3, dash: "solid" },
      editable: true,
    },
  ];

  const layout = {
    autosize: false,
    width: 640,
    height: 640,
    margin: { l: 60, r: 10, t: 50, b: 60 },
    title: { text: "NMA · Thresholds", x: 0.5, xanchor: "center" },
    xaxis: { title: "NII", range: [graphLimits[2], graphLimits[3]], fixedrange: true },
    yaxis: { title: "Area", range: [graphLimits[0], graphLimits[1]], fixedrange: true },
    shapes,
    annotations: withLabels
      ? buildQuadrantAnnotations(
          graphLimits,
          thresholds,
          stats,
          sdArea,
          computeQuadrantPercentages(traces, thresholds, stats, sdArea)
        )
      : [],
  };

  return { data, layout };
}

export default function App() {
  const [activeModule, setActiveModule] = useState("Home");
  const [homeSection, setHomeSection] = useState("about");
  const homeScrollRef = React.useRef(null);
  const [rows, setRows] = useState(initialNmaRows());
  const [collapsedById, setCollapsedById] = useState({});

  const [step, setStep] = useState(0);
  const [controlGateReady, setControlGateReady] = useState(false);
  const [controlGateSd, setControlGateSd] = useState("2");
  const [controlGateBounds, setControlGateBounds] = useState({ x_min: "", x_max: "", y_min: "", y_max: "" });
  const [controlGateMeta, setControlGateMeta] = useState(null);
  const [controlGateFigure, setControlGateFigure] = useState(null);
  const [step1Ready, setStep1Ready] = useState(false);
  const [status, setStatus] = useState("");
  const [statusLevel, setStatusLevel] = useState("info");

  const [step1Figure, setStep1Figure] = useState(null);
  const [step1Stats, setStep1Stats] = useState(null);
  const [step1GraphLimits, setStep1GraphLimits] = useState(null);
  const [step1Sample, setStep1Sample] = useState(null);

  const [sdArea, setSdArea] = useState(1.0);
  const [sdNii, setSdNii] = useState(1.0);

  const [thresholds, setThresholds] = useState({
    v_up: 0,
    v_mid: 0,
    v_down: 0,
    v_down2: 0,
    y_high: 0,
    y_low: 0,
  });

  const [step2Figure, setStep2Figure] = useState(null);
  const [step2Traces, setStep2Traces] = useState(null);
  const [step2Stats, setStep2Stats] = useState(null);
  const [step2GraphLimits, setStep2GraphLimits] = useState(null);
  const [finalMode, setFinalMode] = useState(false);
  const [downloadReady, setDownloadReady] = useState(false);
  const [step2Percentages, setStep2Percentages] = useState(null);
  const [showPlotConfig, setShowPlotConfig] = useState(false);
  const [highlightPlotConfig, setHighlightPlotConfig] = useState(false);
  const [plotConfig, setPlotConfig] = useState({
    ...initialPlotConfig(),
  });
  const [plotSavePath, setPlotSavePath] = useState("");
  const [plotJob, setPlotJob] = useState(() => ({ ...DEFAULT_PLOT_JOB, ...readStorage(STORAGE_KEYS.plotJob, {}) }));
  const [currentPlotIndex, setCurrentPlotIndex] = useState(0);
  const [showNmaPreviewWhilePlotting, setShowNmaPreviewWhilePlotting] = useState(false);
  const [showPlotProgress, setShowPlotProgress] = useState(false);
  const [segJob, setSegJob] = useState(() => ({ ...DEFAULT_SEG_JOB, ...readStorage(STORAGE_KEYS.segJob, {}) }));
  const [regJob, setRegJob] = useState(() => ({ ...DEFAULT_REG_JOB, ...readStorage(STORAGE_KEYS.regJob, {}) }));
  const [fociJob, setFociJob] = useState(() => ({ ...DEFAULT_FOCI_JOB, ...readStorage(STORAGE_KEYS.fociJob, {}) }));
  const [segPreviewNonce, setSegPreviewNonce] = useState(0);
  const [segPreviewPage, setSegPreviewPage] = useState(0);
  const [lastSegPreviewPayload, setLastSegPreviewPayload] = useState(null);
  const [segPanelResetKey, setSegPanelResetKey] = useState(0);
  const [regPanelResetKey, setRegPanelResetKey] = useState(0);
  const [fociPanelResetKey, setFociPanelResetKey] = useState(0);
  const [plotData, setPlotData] = useState(initialPlotDataState);
  const [plotDataStatus, setPlotDataStatus] = useState({ level: "info", text: "" });
  const [plotDataLoading, setPlotDataLoading] = useState(false);
  const [clustering, setClustering] = useState(initialClusteringState);
  const [clusteringStatus, setClusteringStatus] = useState({ level: "info", text: "" });
  const [clusteringLoading, setClusteringLoading] = useState(false);
  const [clusteringElbowLoading, setClusteringElbowLoading] = useState(false);
  const [statsState, setStatsState] = useState(initialStatsState);
  const [statsStatus, setStatsStatus] = useState({ level: "info", text: "" });
  const [statsLoading, setStatsLoading] = useState(false);
  const [gatingState, setGatingState] = useState(initialGatingState);
  const [gatingStatus, setGatingStatus] = useState({ level: "info", text: "" });
  const [gatingLoading, setGatingLoading] = useState(false);
  const [gatingApplying, setGatingApplying] = useState(false);
  const [trackingState, setTrackingState] = useState(initialTrackingState);
  const [trackingStatus, setTrackingStatus] = useState({ level: "info", text: "" });
  const [trackingRunning, setTrackingRunning] = useState(false);
  const [trackingLoadingFrame, setTrackingLoadingFrame] = useState(false);
  const [trackingEditing, setTrackingEditing] = useState(false);
  const fileInputRef = React.useRef(null);
  const attemptedColumnsRef = React.useRef(new Set());
  const plotDataColsCacheRef = React.useRef({});
  const clusteringColsCacheRef = React.useRef({});
  const statsColsCacheRef = React.useRef({});
  const statsFilterValuesCacheRef = React.useRef({});
  const gatingColsCacheRef = React.useRef({});
  const trackingColsCacheRef = React.useRef({});
  const gatingRelayoutTimerRef = React.useRef(null);
  const gatingPreviewRequestRef = React.useRef(0);
  const nmaGateRelayoutTimerRef = React.useRef(null);
  const plotDataPathsKey = useMemo(
    () => (plotData.datasets || []).map((d) => String(d.path || "").trim()).join("||"),
    [plotData.datasets]
  );
  const clusteringPathsKey = useMemo(
    () => (clustering.datasets || []).map((d) => String(d.path || "").trim()).join("||"),
    [clustering.datasets]
  );
  const statsPathsKey = useMemo(
    () => (statsState.datasets || []).map((d) => String(d.path || "").trim()).join("||"),
    [statsState.datasets]
  );
  const gatingPathsKey = useMemo(
    () => (gatingState.datasets || []).map((d) => String(d.path || "").trim()).join("||"),
    [gatingState.datasets]
  );
  const trackingTablePath = useMemo(
    () => String(trackingState.path_to_table || "").trim(),
    [trackingState.path_to_table]
  );
  const hasPlotRun = Boolean(plotJob.job_id);
  const hasSegSession =
    Boolean(segJob.job_id) ||
    (segJob.status && segJob.status !== "idle") ||
    Boolean(segJob.error) ||
    Boolean(segJob.log) ||
    Boolean(segJob.preview_path) ||
    ((segJob.preview_paths || []).length > 0);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.activeModule, JSON.stringify(activeModule));
  }, [activeModule]);

  const handleSelectHomeSection = (sectionId) => {
    setHomeSection(sectionId);
    if (typeof window === "undefined") return;
    window.requestAnimationFrame(() => {
      const target = document.getElementById(`home-${sectionId}`);
      const scrollHost = homeScrollRef.current;
      if (target && scrollHost) {
        const hostRect = scrollHost.getBoundingClientRect();
        const targetRect = target.getBoundingClientRect();
        scrollHost.scrollTo({
          top: scrollHost.scrollTop + targetRect.top - hostRect.top,
          behavior: "smooth",
        });
      }
    });
  };

  const handleOpenTutorial = (moduleName) => {
    const sectionId = MODULE_TUTORIAL_SECTION[moduleName];
    setActiveModule("Home");
    if (!sectionId) return;
    setHomeSection(sectionId);
    if (typeof window === "undefined") return;
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        const target = document.getElementById(`home-${sectionId}`);
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  };

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.plotJob, JSON.stringify(plotJob));
  }, [plotJob]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.segJob, JSON.stringify(segJob));
  }, [segJob]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.regJob, JSON.stringify(regJob));
  }, [regJob]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.fociJob, JSON.stringify(fociJob));
  }, [fociJob]);

  const datasets = useMemo(() => buildDatasets(rows), [rows]);
  const allDetectedColumns = useMemo(
    () => Array.from(new Set(rows.flatMap((r) => (r.columns || []).map((c) => String(c))))).sort(),
    [rows]
  );
  const hasControl = datasets.some((d) => d.is_control);

  const updateRow = (idx, patch) => {
    setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  };

  const addRow = () => setRows((prev) => [...prev, emptyRow()]);
  const removeRow = (idx) => setRows((prev) => prev.filter((_, i) => i !== idx));
  const toggleDatasetCollapse = (rowId) => {
    setCollapsedById((prev) => ({ ...prev, [rowId]: !prev[rowId] }));
  };
  const setAllCollapsed = (collapsed) => {
    setCollapsedById(
      Object.fromEntries(rows.map((r) => [r.id, collapsed]))
    );
  };

  const callApi = async (path, payload) => {
    let res;
    try {
      res = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (err) {
      if (err instanceof TypeError) {
        throw new Error("Failed to fetch API. Check if backend is running at http://127.0.0.1:8000.");
      }
      throw err;
    }
    if (!res.ok) {
      throw new Error(await errorFromResponse(res, "API request failed."));
    }
    return res.json();
  };

  const setPlotDataStatusMsg = (text, level = "info") => {
    setPlotDataStatus({ text, level });
  };

  const requireNmaAxes = () => {
    const missing = datasets.filter((dataset) => !dataset.area_col || !dataset.nii_col);
    if (missing.length === 0) return true;
    const names = missing.map((dataset) => dataset.name || dataset.path.split("/").pop()).join(", ");
    setStatus(`Choose both Area and NII columns for: ${names}. Open each dataset row and select the columns that contain those numeric measurements.`);
    setStatusLevel("error");
    return false;
  };

  const parseNmaOptionalNumber = (value) => {
    if (value === "" || value == null) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  };

  const makeControlGatePayload = (overrideBounds = null) => {
    const sd = Number(controlGateSd);
    const bounds = overrideBounds || controlGateBounds;
    return {
      enabled: true,
      sd: Number.isFinite(sd) && sd > 0 ? sd : 2,
      x_min: parseNmaOptionalNumber(bounds.x_min),
      x_max: parseNmaOptionalNumber(bounds.x_max),
      y_min: parseNmaOptionalNumber(bounds.y_min),
      y_max: parseNmaOptionalNumber(bounds.y_max),
    };
  };

  const markControlGateDirty = () => {
    setControlGateReady(false);
    setStep1Ready(false);
    setStep(0);
    setStep1Figure(null);
    setStep1Stats(null);
    setStep1GraphLimits(null);
    setStep1Sample(null);
    setStep2Figure(null);
    setStep2Traces(null);
    setStep2Stats(null);
    setStep2GraphLimits(null);
    setStep2Percentages(null);
    setFinalMode(false);
    setDownloadReady(false);
    setShowPlotConfig(false);
  };

  useEffect(() => {
    if (!showPlotConfig) return;
    const targets = rows
      .map((row, idx) => ({ row, idx }))
      .filter(({ row }) => {
        const p = row.path?.trim();
        if (!p) return false;
        if ((row.columns || []).length > 0) return false;
        return !attemptedColumnsRef.current.has(p);
      });

    if (targets.length === 0) return;
    let cancelled = false;

    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ row, idx }) => {
          const path = row.path.trim();
          attemptedColumnsRef.current.add(path);
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            return {
              idx,
              columns: res.columns || [],
              areaColumns: res.area_columns || [],
              niiColumns: res.nii_columns || [],
            };
          } catch {
            return { idx, columns: [], areaColumns: [], niiColumns: [] };
          }
        })
      );

      if (cancelled) return;
      setRows((prev) =>
        prev.map((r, i) => {
          const hit = loaded.find((x) => x.idx === i);
          if (!hit || hit.columns.length === 0) return r;
          const areaGuess = pickNmaMeasureColumn(hit.columns, "Area", r.area_col, hit.areaColumns);
          const niiGuess = pickNmaMeasureColumn(hit.columns, "NII", r.nii_col, hit.niiColumns);
          return {
            ...r,
            columns: hit.columns,
            area_columns: hit.areaColumns,
            nii_columns: hit.niiColumns,
            area_col: r.area_col && hit.columns.includes(r.area_col) ? r.area_col : areaGuess,
            nii_col: r.nii_col && hit.columns.includes(r.nii_col) ? r.nii_col : niiGuess,
          };
        })
      );
    })();

    return () => {
      cancelled = true;
    };
  }, [rows, showPlotConfig]);

  useEffect(() => {
    const datasets = plotData.datasets || [];
    const targets = datasets
      .map((d, idx) => ({ d, idx }))
      .filter(({ d }) => String(d.path || "").trim());
    if (targets.length === 0) {
      setPlotData((prev) => {
        if ((prev.columns || []).length === 0 && (prev.categoricalColumns || []).length === 0 && (prev.controlOptions || []).length === 0 && !prev.columnsWarning) return prev;
        return { ...prev, columns: [], categoricalColumns: [], controlOptions: [], columnsWarning: "" };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ d, idx }) => {
          const path = String(d.path || "").trim();
          if (plotDataColsCacheRef.current[path]) {
            return { idx, path, ...plotDataColsCacheRef.current[path] };
          }
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            const cols = res.columns || [];
            const categorical = res.categorical_columns || [];
            plotDataColsCacheRef.current[path] = { columns: cols, categorical };
            return { idx, path, columns: cols, categorical };
          } catch {
            return { idx, path, columns: [], categorical: [] };
          }
        })
      );
      if (cancelled) return;
      const valid = loaded.filter((x) => x.columns.length > 0);
      const firstCols = valid[0]?.columns || [];
      const firstCategorical = valid[0]?.categorical || [];
      const mismatch = valid.some((x) =>
        x.columns.length !== firstCols.length ||
        x.columns.some((c, i) => c !== firstCols[i])
      );
      setPlotData((prev) => {
        const nextDatasets = (prev.datasets || []).map((d, i) => {
          const hit = loaded.find((x) => x.idx === i);
          if (!hit) return d;
          if (sameArray(d.columns || [], hit.columns || [])) return d;
          return { ...d, columns: hit.columns };
        });
        const keepIfExists = (key) => (firstCols.includes(prev[key]) ? prev[key] : "");
        const nextWarning = mismatch
          ? "CSV columns are not identical. Use files with exactly the same columns and order."
          : "";
        const didDatasetsChange = nextDatasets.some((d, i) => d !== (prev.datasets || [])[i]);
        const sameColumns = sameArray(prev.columns || [], firstCols || []);
        const sameCategorical = sameArray(prev.categoricalColumns || [], firstCategorical || []);
        const sameAxes =
          keepIfExists("x") === prev.x &&
          keepIfExists("y") === prev.y &&
          keepIfExists("hue") === prev.hue &&
          keepIfExists("size") === prev.size;
        if (!didDatasetsChange && sameColumns && sameCategorical && sameAxes && nextWarning === (prev.columnsWarning || "")) {
          return prev;
        }
        return {
          ...prev,
          datasets: nextDatasets,
          columns: firstCols,
          categoricalColumns: firstCategorical,
          x: keepIfExists("x"),
          y: keepIfExists("y"),
          hue: keepIfExists("hue"),
          size: keepIfExists("size"),
          columnsWarning: nextWarning,
        };
      });
      try {
        const condRes = await callApi("/graphs/conditions", {
          datasets: targets.map(({ d }) => ({
            name: String(d.name || "").trim(),
            path: String(d.path || "").trim(),
          })),
        });
        if (cancelled) return;
        const nextConditions = condRes.conditions || [];
        setPlotData((prev) => {
          const validControl = prev.control && nextConditions.includes(prev.control) ? prev.control : "";
          if (sameArray(prev.controlOptions || [], nextConditions) && prev.control === validControl) return prev;
          return { ...prev, controlOptions: nextConditions, control: validControl };
        });
      } catch {
        if (cancelled) return;
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [plotDataPathsKey]);

  useEffect(() => {
    const datasets = clustering.datasets || [];
    const targets = datasets
      .map((d, idx) => ({ d, idx }))
      .filter(({ d }) => String(d.path || "").trim());
    if (targets.length === 0) {
      setClustering((prev) => {
        if ((prev.columnsAll || []).length === 0 && (prev.numericColumns || []).length === 0 && (prev.columns || []).length === 0) return prev;
        return { ...prev, columnsAll: [], numericColumns: [], columns: [] };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ d, idx }) => {
          const path = String(d.path || "").trim();
          if (clusteringColsCacheRef.current[path]) {
            return { idx, ...clusteringColsCacheRef.current[path] };
          }
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            const payload = {
              columns: res.columns || [],
              numeric: res.numeric_columns || [],
            };
            clusteringColsCacheRef.current[path] = payload;
            return { idx, ...payload };
          } catch {
            return { idx, columns: [], numeric: [] };
          }
        })
      );
      if (cancelled) return;
      const valid = loaded.filter((x) => x.columns.length > 0);
      const firstCols = valid[0]?.columns || [];
      const firstNumeric = valid[0]?.numeric || [];
      setClustering((prev) => {
        const keepNumeric = (prev.columns || []).filter((c) => firstNumeric.includes(c));
        const changed =
          !sameArray(prev.columnsAll || [], firstCols) ||
          !sameArray(prev.numericColumns || [], firstNumeric) ||
          !sameArray(prev.columns || [], keepNumeric);
        if (!changed) return prev;
        return {
          ...prev,
          columnsAll: firstCols,
          numericColumns: firstNumeric,
          columns: keepNumeric.length ? keepNumeric : firstNumeric.slice(0, Math.min(8, firstNumeric.length)),
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [clusteringPathsKey]);

  useEffect(() => {
    const datasets = statsState.datasets || [];
    const targets = datasets
      .map((d, idx) => ({ d, idx }))
      .filter(({ d }) => String(d.path || "").trim());
    if (targets.length === 0) {
      setStatsState((prev) => {
        if ((prev.columns || []).length === 0) return prev;
        return {
          ...prev,
          columns: [],
          categoricalColumns: [],
          numeric_col: "",
          group_col: "",
          group_col1: "",
          group_col2: "",
          category_col: "",
          condition_col: "",
          filters: (prev.filters || [makeStatsFilterRow()]).map((filter) => ({ ...filter, column: "", values: [] })),
          filterValueOptions: {},
        };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ d, idx }) => {
          const path = String(d.path || "").trim();
          if (statsColsCacheRef.current[path]) {
            return { idx, ...statsColsCacheRef.current[path] };
          }
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            const entry = {
              columns: res.columns || [],
              categoricalColumns: res.categorical_columns || [],
            };
            statsColsCacheRef.current[path] = entry;
            return { idx, ...entry };
          } catch {
            return { idx, columns: [], categoricalColumns: [] };
          }
        })
      );
      if (cancelled) return;
      const valid = loaded.filter((x) => x.columns.length > 0);
      const firstCols = valid[0]?.columns || [];
      const firstCategorical = valid[0]?.categoricalColumns || [];
      setStatsState((prev) => {
        const keep = (k) => (prev[k] && firstCols.includes(prev[k]) ? prev[k] : "");
        const nextFilters = (prev.filters || [makeStatsFilterRow()]).map((filter) => {
          if (!filter.column || firstCols.includes(filter.column)) {
            return filter;
          }
          return { ...filter, column: "", values: [] };
        });
        const nextFilterValueOptions = Object.fromEntries(
          Object.entries(prev.filterValueOptions || {}).filter(([column]) => firstCols.includes(column))
        );
        if (sameArray(prev.columns || [], firstCols || [])
          && sameArray(prev.categoricalColumns || [], firstCategorical || [])
          && keep("numeric_col") === prev.numeric_col
          && keep("group_col") === prev.group_col
          && keep("group_col1") === prev.group_col1
          && keep("group_col2") === prev.group_col2
          && keep("category_col") === prev.category_col
          && keep("condition_col") === prev.condition_col
          && JSON.stringify(nextFilters) === JSON.stringify(prev.filters || [])
          && JSON.stringify(nextFilterValueOptions) === JSON.stringify(prev.filterValueOptions || {})) return prev;
        return {
          ...prev,
          columns: firstCols,
          categoricalColumns: firstCategorical,
          numeric_col: keep("numeric_col"),
          group_col: keep("group_col"),
          group_col1: keep("group_col1"),
          group_col2: keep("group_col2"),
          category_col: keep("category_col"),
          condition_col: keep("condition_col"),
          filters: nextFilters,
          filterValueOptions: nextFilterValueOptions,
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [statsPathsKey]);

  useEffect(() => {
    const paths = (statsState.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => String(d.path || "").trim())
      .filter(Boolean);
    const filterColumns = Array.from(new Set(
      (statsState.filters || [])
        .map((filter) => String(filter.column || "").trim())
        .filter(Boolean)
    ));

    if (!paths.length || !filterColumns.length) {
      setStatsState((prev) => {
        if (!Object.keys(prev.filterValueOptions || {}).length) return prev;
        const keepColumns = new Set(
          (prev.filters || [])
            .map((filter) => String(filter.column || "").trim())
            .filter(Boolean)
        );
        const nextOptions = Object.fromEntries(
          Object.entries(prev.filterValueOptions || {}).filter(([column]) => keepColumns.has(column))
        );
        if (JSON.stringify(nextOptions) === JSON.stringify(prev.filterValueOptions || {})) return prev;
        const nextFilters = (prev.filters || []).map((filter) => {
          const opts = nextOptions[filter.column] || [];
          return opts.length ? { ...filter, values: (filter.values || []).filter((value) => opts.includes(value)) } : filter;
        });
        return { ...prev, filters: nextFilters, filterValueOptions: nextOptions };
      });
      return;
    }

    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        filterColumns.map(async (column) => {
          const cacheKey = `${paths.join("||")}::${column}`;
          if (statsFilterValuesCacheRef.current[cacheKey]) {
            return { column, values: statsFilterValuesCacheRef.current[cacheKey] };
          }
          try {
            const res = await callApi("/datasets/column-values", { paths, column, limit: 200 });
            const values = (res.values || []).map(normalizeFilterOption).filter(Boolean);
            statsFilterValuesCacheRef.current[cacheKey] = values;
            return { column, values };
          } catch {
            return { column, values: [] };
          }
        })
      );
      if (cancelled) return;
      setStatsState((prev) => {
        const nextOptions = { ...(prev.filterValueOptions || {}) };
        for (const item of loaded) {
          nextOptions[item.column] = item.values || [];
        }
        const nextFilters = (prev.filters || []).map((filter) => {
          const opts = nextOptions[filter.column] || [];
          return {
            ...filter,
            values: (filter.values || []).filter((value) => opts.includes(value)),
          };
        });
        if (JSON.stringify(nextOptions) === JSON.stringify(prev.filterValueOptions || {})
          && JSON.stringify(nextFilters) === JSON.stringify(prev.filters || [])) return prev;
        return { ...prev, filters: nextFilters, filterValueOptions: nextOptions };
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [statsState.datasets, statsState.filters]);

  useEffect(() => {
    const datasets = gatingState.datasets || [];
    const targets = datasets
      .map((d, idx) => ({ d, idx }))
      .filter(({ d }) => String(d.path || "").trim());
    if (targets.length === 0) {
      setGatingState((prev) => {
        if ((prev.columns || []).length === 0 && (prev.numericColumns || []).length === 0) return prev;
        return { ...prev, columns: [], numericColumns: [], x_col: "", y_col: "" };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      const loaded = await Promise.all(
        targets.map(async ({ d, idx }) => {
          const path = String(d.path || "").trim();
          if (gatingColsCacheRef.current[path]) {
            return { idx, ...gatingColsCacheRef.current[path] };
          }
          try {
            const res = await callApi("/nma/datasets/columns", { path });
            const payload = {
              columns: res.columns || [],
              numeric: res.numeric_columns || [],
            };
            gatingColsCacheRef.current[path] = payload;
            return { idx, ...payload };
          } catch {
            return { idx, columns: [], numeric: [] };
          }
        })
      );
      if (cancelled) return;
      const valid = loaded.filter((x) => x.columns.length > 0);
      const firstCols = valid[0]?.columns || [];
      const firstNumeric = valid[0]?.numeric || [];
      setGatingState((prev) => {
        const keep = (k) => (prev[k] && firstNumeric.includes(prev[k]) ? prev[k] : "");
        if (
          sameArray(prev.columns || [], firstCols) &&
          sameArray(prev.numericColumns || [], firstNumeric) &&
          keep("x_col") === prev.x_col &&
          keep("y_col") === prev.y_col
        ) return prev;
        return {
          ...prev,
          columns: firstCols,
          numericColumns: firstNumeric,
          x_col: keep("x_col"),
          y_col: keep("y_col"),
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [gatingPathsKey]);

  useEffect(() => {
    const path = trackingTablePath;
    if (!path) {
      setTrackingState((prev) => {
        if ((prev.columns || []).length === 0 && !prev.image_col) return prev;
        return { ...prev, columns: [], image_col: "" };
      });
      return;
    }
    let cancelled = false;
    (async () => {
      let cols = [];
      if (trackingColsCacheRef.current[path]) {
        cols = trackingColsCacheRef.current[path];
      } else {
        try {
          const res = await callApi("/nma/datasets/columns", { path });
          cols = res.columns || [];
          trackingColsCacheRef.current[path] = cols;
        } catch {
          cols = [];
        }
      }
      if (cancelled) return;
      setTrackingState((prev) => {
        const imgCols = (cols || []).filter((c) => String(c || "").toLowerCase().includes("image_name"));
        const keepImageCol = prev.image_col && imgCols.includes(prev.image_col) ? prev.image_col : "";
        if (sameArray(prev.columns || [], cols) && keepImageCol === prev.image_col) return prev;
        return {
          ...prev,
          columns: cols,
          image_col: keepImageCol,
        };
      });
    })();
    return () => {
      cancelled = true;
    };
  }, [trackingTablePath]);

  const handleDownloadTable = () => {
    if (!step2Percentages) return;
    const quadrantOrder = ["LR", "LI", "N", "I", "SR", "S", "SI"];
    const datasetNames = Array.from(
      new Set(
        Object.values(step2Percentages)
          .flatMap((v) => Object.keys(v))
          .concat((step2Traces || []).map((t) => t.name).filter(Boolean))
      )
    );
    const header = ["Quadrant", ...datasetNames];
    const lines = [header.map(csvCell).join(",")];
    quadrantOrder.forEach((q) => {
      const row = [q];
      datasetNames.forEach((name) => {
        const val = step2Percentages[q]?.[name];
        row.push(val != null ? val.toFixed(1) : "");
      });
      lines.push(row.map(csvCell).join(","));
    });
    const blob = new Blob([`${lines.join("\n")}\n`], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "quadrant_proportions.csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadStatsTableCsv = (table) => {
    if (!table?.columns?.length) return;
    const cols = table.columns.map((c) => String(c));
    const lines = [cols.map(csvCell).join(",")];
    (table.rows || []).forEach((row) => {
      const vals = cols.map((c) => csvCell(row?.[c] ?? ""));
      lines.push(vals.join(","));
    });
    const blob = new Blob([`${lines.join("\n")}\n`], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const name = String(table.name || "stats_result").replace(/\s+/g, "_").toLowerCase();
    a.href = url;
    a.download = `${name}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadStatsLogTxt = () => {
    const text = String(statsState.log || "");
    if (!text.trim()) return;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "statistics_log.txt";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const copyStatsLogTxt = async () => {
    const text = String(statsState.log || "");
    if (!text.trim()) return;
    await copyText(text);
  };

  const pickCsvPath = async () => {
    const res = await fetch(`${API_BASE}/system/pick-csv`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error(await errorFromResponse(res, "Could not open the CSV file picker."));
    }
    return res.json();
  };

  const pickDirectoryPath = async () => {
    const res = await fetch(`${API_BASE}/system/pick-directory`, {
      method: "POST",
    });
    if (!res.ok) {
      throw new Error(await errorFromResponse(res, "Could not open the folder picker."));
    }
    return res.json();
  };

  const handleStartSegmentation = async (payload) => {
    if (["starting", "queued", "running", "canceling"].includes(segJob.status)) {
      return;
    }
    scrollToTopSmooth();
    setStatus("Starting segmentation...");
    setStatusLevel("info");
    setSegJob((prev) => ({
      ...prev,
      status: "starting",
      message: "Starting...",
      error: "",
    }));
    try {
      if (payload?.preview) {
        setLastSegPreviewPayload(payload);
      }
      const res = await callApi("/segmentation/start", payload);
      setSegJob({
        job_id: res.job_id,
        status: res.status || "queued",
        progress: 0,
        message: "Queued",
        log: "",
        preview_path: "",
        preview_paths: [],
        preview_index: payload?.preview_index ?? null,
        error: "",
      });
      setSegPreviewNonce((n) => n + 1);
    } catch (err) {
      setSegJob((prev) => ({ ...prev, status: "idle" }));
      setStatus(errorMessageFromException(err, "Segmentation could not start. Check the image folders, output folder, and selected channels."));
      setStatusLevel("error");
    }
  };

  const handleStopSegmentation = async () => {
    if (!segJob.job_id || segJob.status === "canceling") return;
    const previousStatus = segJob.status;
    setSegJob((prev) => ({ ...prev, status: "canceling", message: "Stopping..." }));
    try {
      const res = await fetch(`${API_BASE}/segmentation/stop/${segJob.job_id}`, { method: "POST" });
      if (!res.ok) {
        throw new Error(await errorFromResponse(res, "Could not stop segmentation."));
      }
      setSegJob((prev) => ({ ...prev, status: "canceling", message: "Stopping after current image..." }));
    } catch (err) {
      setSegJob((prev) => ({ ...prev, status: previousStatus, message: "Stop could not be requested." }));
      setStatus(errorMessageFromException(err, "The stop request could not be sent. Wait a moment and try Stop again."));
      setStatusLevel("error");
    }
  };

  const handleStartRegistration = async (payload) => {
    if (["starting", "queued", "running", "canceling"].includes(regJob.status)) {
      return;
    }
    const rows = payload?.images_data?.rows || [];
    const channels = payload?.images_data?.channels || [];
    const idToName = Object.fromEntries(channels.map((c) => [c.id, c.name || c.id]));
    const savePath = String(payload?.reg_data?.save_path || "").trim();
    const reference = payload?.reg_data?.reference;
    const moving = payload?.reg_data?.moving || [];
    const errs = [];
    if (!savePath) errs.push("Choose a Saving path before running registration.");
    if (!reference) errs.push("Select the reference channel that the other channels should align to.");
    if (!rows.length) errs.push("No image conditions are loaded. Click Load images and save the condition/channel table first.");
    rows.forEach((r, idx) => {
      [reference, ...moving].filter(Boolean).forEach((chId) => {
        if (!String(r[chId] || "").trim()) {
          errs.push(`Row ${idx + 1}, ${idToName[chId] || chId}: choose the image folder before running registration.`);
        }
      });
    });
    if (errs.length) {
      setStatus(errs.join("\n"));
      setStatusLevel("error");
      return;
    }
    scrollToTopSmooth();
    setStatus("Starting registration...");
    setStatusLevel("info");
    setRegJob((prev) => ({ ...prev, status: "starting", message: "Starting...", error: "" }));
    try {
      const res = await callApi("/registration/start", payload);
      setRegJob({
        job_id: res.job_id,
        status: res.status || "queued",
        progress: 0,
        done: 0,
        total: 0,
        message: "Queued",
        log: "",
        error: "",
      });
    } catch (err) {
      setRegJob((prev) => ({ ...prev, status: "idle" }));
      setStatus(errorMessageFromException(err, "Registration could not start. Check the selected image folders, reference channel, moving channels, and saving path."));
      setStatusLevel("error");
    }
  };

  const handleStopRegistration = async () => {
    if (!regJob.job_id) return;
    try {
      const res = await fetch(`${API_BASE}/registration/stop/${regJob.job_id}`, { method: "POST" });
      if (!res.ok) {
        throw new Error(await errorFromResponse(res, "Could not stop registration."));
      }
      setRegJob((prev) => ({ ...prev, status: "canceling", message: "Stop requested..." }));
      setStatus("Registration stop requested...");
      setStatusLevel("info");
    } catch (err) {
      setStatus(errorMessageFromException(err, "The registration stop request could not be sent. Wait a moment and try Stop again."));
      setStatusLevel("error");
    }
  };

  const loadFociChannels = async (pkl_path) => {
    const res = await callApi("/foci/channels", { pkl_path });
    return (res.channels || []).map((c) => ({ label: c, value: c }));
  };

  const handleStartFoci = async (payload) => {
    if (["starting", "queued", "running", "canceling"].includes(fociJob.status)) return;
    scrollToTopSmooth();
    setStatus("Starting foci overlay...");
    setStatusLevel("info");
    setFociJob((prev) => ({ ...prev, status: "starting", message: "Starting...", error: "" }));
    try {
      const res = await callApi("/foci/start", payload);
      setFociJob({
        job_id: res.job_id,
        status: res.status || "queued",
        progress: 0,
        message: "Queued",
        log: "",
        error: "",
      });
    } catch (err) {
      setFociJob((prev) => ({ ...prev, status: "idle" }));
      setStatus(errorMessageFromException(err, "Foci overlay could not start. Check the Pickles folder, output folder, selected channels, and actions."));
      setStatusLevel("error");
    }
  };

  const handleStopFoci = async () => {
    if (!fociJob.job_id) return;
    try {
      const res = await fetch(`${API_BASE}/foci/stop/${fociJob.job_id}`, { method: "POST" });
      if (!res.ok) {
        throw new Error(await errorFromResponse(res, "Could not stop foci overlay."));
      }
      setFociJob((prev) => ({ ...prev, status: "canceling", message: "Stop requested..." }));
      setStatus("Foci stop requested...");
      setStatusLevel("info");
    } catch (err) {
      setStatus(errorMessageFromException(err, "The foci overlay stop request could not be sent. Wait a moment and try Stop again."));
      setStatusLevel("error");
    }
  };

  const handleResetSegmentationUi = () => {
    setSegJob({ ...DEFAULT_SEG_JOB });
    setSegPreviewPage(0);
    setSegPreviewNonce((n) => n + 1);
    setLastSegPreviewPayload(null);
    setStatus("");
    setStatusLevel("info");
    setSegPanelResetKey((k) => k + 1);
  };

  const handleControlGate = async ({ overrideBounds = null, fromDrag = false } = {}) => {
    if (!requireNmaAxes()) return false;
    setShowPlotConfig(false);
    if (!fromDrag) {
      scrollToTopSmooth();
      setStep(0);
    }
    setStatus(fromDrag ? "Updating the manual control gate..." : "Opening Step 1: draw the control gate...");
    setStatusLevel("info");
    try {
      const payload = {
        params: { datasets },
        sample_per_ds: 2000,
        control_gate: makeControlGatePayload(overrideBounds),
      };
      const data = await callApi("/nma/settings/compute", payload);
      const graphLimits = data.axis ? [data.axis.y[0], data.axis.y[1], data.axis.x[0], data.axis.x[1]] : null;
      setControlGateMeta(data.gate || null);
      if (data.gate?.bounds) {
        setControlGateBounds({
          x_min: String(data.gate.bounds.x_min ?? ""),
          x_max: String(data.gate.bounds.x_max ?? ""),
          y_min: String(data.gate.bounds.y_min ?? ""),
          y_max: String(data.gate.bounds.y_max ?? ""),
        });
      }
      setControlGateFigure(buildControlGateFigure(data.gate, data.stats, graphLimits));
      setControlGateReady(true);
      setStep1Ready(false);
      setStep1Figure(null);
      setStep1Stats(null);
      setStep1GraphLimits(null);
      setStep1Sample(null);
      setStep2Figure(null);
      setStep2Traces(null);
      setStep2Stats(null);
      setStep2GraphLimits(null);
      setStep2Percentages(null);
      setFinalMode(false);
      const kept = data.gate?.kept ?? 0;
      const total = data.gate?.total ?? 0;
      const pct = Number(data.gate?.kept_percent ?? 0).toFixed(1);
      setStatus(`Step 1 gate ready: ${kept}/${total} control cells kept (${pct}%). Adjust the box if needed, then continue to Step 2.`);
      setStatusLevel("success");
      return true;
    } catch (err) {
      setStatus(errorMessageFromException(err, "The control gate could not be created. Check that the control dataset has numeric Area/NII values, then draw a wider gate around the cells of interest."));
      setStatusLevel("error");
      return false;
    }
  };

  const handleNmaGateRelayout = (evt) => {
    if (!evt || !controlGateMeta?.bounds) return;
    const shape0 = evt["shapes[0]"];
    const pick = (keyA, keyB, fallback) => {
      const a = evt[keyA];
      const b = evt[keyB];
      if (a != null) return a;
      if (b != null) return b;
      return fallback;
    };
    const nextX0 = shape0?.x0 ?? pick("shapes[0].x0", "shapes[0].x1", controlGateBounds.x_min);
    const nextX1 = shape0?.x1 ?? pick("shapes[0].x1", "shapes[0].x0", controlGateBounds.x_max);
    const nextY0 = shape0?.y0 ?? pick("shapes[0].y0", "shapes[0].y1", controlGateBounds.y_min);
    const nextY1 = shape0?.y1 ?? pick("shapes[0].y1", "shapes[0].y0", controlGateBounds.y_max);
    if (nextX0 == null || nextX1 == null || nextY0 == null || nextY1 == null) return;

    const xMin = Math.min(Number(nextX0), Number(nextX1));
    const xMax = Math.max(Number(nextX0), Number(nextX1));
    const yMin = Math.min(Number(nextY0), Number(nextY1));
    const yMax = Math.max(Number(nextY0), Number(nextY1));
    if (![xMin, xMax, yMin, yMax].every((n) => Number.isFinite(n))) return;

    const nextBounds = {
      x_min: String(xMin),
      x_max: String(xMax),
      y_min: String(yMin),
      y_max: String(yMax),
    };
    setControlGateBounds(nextBounds);
    setControlGateReady(false);
    setStep1Ready(false);
    setStep2Figure(null);
    setStep2Traces(null);
    setStep2Stats(null);
    setStep2GraphLimits(null);
    setStep2Percentages(null);
    setFinalMode(false);

    if (nmaGateRelayoutTimerRef.current) {
      clearTimeout(nmaGateRelayoutTimerRef.current);
      nmaGateRelayoutTimerRef.current = null;
    }
    nmaGateRelayoutTimerRef.current = setTimeout(() => {
      handleControlGate({ overrideBounds: nextBounds, fromDrag: true });
    }, 220);
  };

  const handleStep1 = async () => {
    if (!requireNmaAxes()) return;
    if (!controlGateReady) {
      setStatus("Create the Step 1 control gate first. Step 2 needs the normal control cells selected before it can draw the ellipse.");
      setStatusLevel("error");
      setStep(0);
      return;
    }
    setShowPlotConfig(false);
    setStatus("Computing Step 2 ellipse...");
    setStatusLevel("info");
    try {
      const payload = {
        params: { datasets },
        sample_per_ds: 2000,
        control_gate: makeControlGatePayload(),
      };
      const data = await callApi("/nma/settings/compute", payload);
      setStep1Sample(data.sample);
      setStep1Stats(data.stats);
      setStep1GraphLimits(data.axis ? [data.axis.y[0], data.axis.y[1], data.axis.x[0], data.axis.x[1]] : null);
      setSdArea(round2(data.sd_factors.sd_area));
      setSdNii(round2(data.sd_factors.sd_nii));
      const fig = buildStep1Figure(
        data.sample,
        data.stats,
        data.axis ? [data.axis.y[0], data.axis.y[1], data.axis.x[0], data.axis.x[1]] : null,
        data.sd_factors.sd_nii,
        data.sd_factors.sd_area
      );
      setStep1Figure(fig);
      setThresholds(computeThresholds(data.stats, data.sd_factors.sd_nii, data.sd_factors.sd_area));
      setStatus("Step 2 ready. The ellipse is based only on the gated normal control cells.");
      setStatusLevel("success");
      setStep1Ready(true);
      setStep(1);
    } catch (err) {
      setStatus(errorMessageFromException(err, "Step 2 could not be computed. Check that at least one control dataset is selected, the Step 1 gate keeps cells, and Area/NII columns are numeric."));
      setStatusLevel("error");
    }
  };

  const handleAutoDbscan = async () => {
    if (!requireNmaAxes()) return;
    setStatus("Running DBSCAN...");
    setStatusLevel("info");
    try {
      const payload = { params: { datasets }, control_gate: makeControlGatePayload() };
      const data = await callApi("/nma/settings/auto-dbscan", payload);
      setSdNii(round2(data.sd_factors.sd_nii));
      setSdArea(round2(data.sd_factors.sd_area));
      if (step1Stats && step1GraphLimits && step1Sample) {
        setStep1Figure(buildStep1Figure(step1Sample, step1Stats, step1GraphLimits, data.sd_factors.sd_nii, data.sd_factors.sd_area));
      }
      if (step1Stats) {
        setThresholds(computeThresholds(step1Stats, data.sd_factors.sd_nii, data.sd_factors.sd_area));
      }
      setStatus("DBSCAN applied. Update the Step 3 figure.");
      setStatusLevel("success");
    } catch (err) {
      setStatus(errorMessageFromException(err, "DBSCAN could not be applied. Check that the control data has enough valid numeric rows, then try different clustering settings."));
      setStatusLevel("error");
    }
  };

  const handleStep2 = async () => {
    if (!requireNmaAxes()) return false;
    setStatus("Generating Step 3 figure...");
    setStatusLevel("info");
    try {
      const payload = {
        params: { datasets },
        include_sample: true,
        include_all_datasets: true,
        sd_nii: sdNii,
        sd_area: sdArea,
        thresholds,
        control_gate: makeControlGatePayload(),
      };
      const data = await callApi("/nma/settings/figure", payload);
      const traces = (data.figure?.data || []).filter(
        (t) => t?.mode?.includes("markers") || t?.type === "scattergl"
      );
      setStep2Traces(traces);
      const stats = step1Stats || data.stats;
      const graphLimits = data.graph_limits;
      setStep2Stats(stats);
      setStep2GraphLimits(graphLimits);
      setStep2Figure(buildStep2Figure(traces, stats, graphLimits, thresholds, sdNii, sdArea, true));
      setStep2Percentages(computeQuadrantPercentages(traces, thresholds, stats, sdArea));
      setFinalMode(false);
      setStatus("Step 3 ready.");
      setStatusLevel("success");
      return true;
    } catch (err) {
      setStatus(errorMessageFromException(err, "Step 3 figure could not be generated. Check the selected axes, thresholds, and loaded settings."));
      setStatusLevel("error");
      return false;
    }
  };

  const handleComplete = async () => {
    if (!step2Traces || !step2Stats || !step2GraphLimits) {
      setStatus("Generate the Step 3 figure first.");
      setStatusLevel("error");
      return;
    }
    if (!step1Stats) {
      setStatus("Run Step 2 first. Step 3 needs the control ellipse prepared before it can continue.");
      setStatusLevel("error");
      return;
    }
    const fig = buildStep2Figure(
      step2Traces,
      step2Stats,
      step2GraphLimits,
      thresholds,
      sdNii,
      sdArea,
      true,
      "black",
      "black"
    );
    setStep2Figure(fig);
    setFinalMode(true);
    setStep2Percentages(computeQuadrantPercentages(step2Traces, thresholds, step2Stats, sdArea));
    try {
      await callApi("/nma/settings/save", {
        name: datasets.find((d) => d.is_control)?.name || "control",
        mean_nii: step1Stats.mu_x,
        std_nii: step1Stats.sd_x,
        mean_area: step1Stats.mu_y,
        std_area: step1Stats.sd_y,
        sd_nii: sdNii,
        sd_area: sdArea,
        graph_limits: step1GraphLimits || step2GraphLimits || [0, 0, 0, 0],
        thresholds,
      });
      setDownloadReady(true);
      setStatus("Settings ready. Choose the plot style, saving path, and output options in the left panel.");
      setStatusLevel("success");
      focusNmaPlotConfig("success");
    } catch (err) {
      setStatus(errorMessageFromException(err, "The final NMA figure could not be completed. Check the selected graph limits and settings."));
      setStatusLevel("error");
    }
  };

  const handleLoadSettings = async (file) => {
    setStatus("Loading settings...");
    setStatusLevel("info");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API_BASE}/nma/settings/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        throw new Error(await errorFromResponse(res, "Could not load the settings file."));
      }
      const data = await res.json();

      // Apply settings
      setSdArea(round2(data.sd_area));
      setSdNii(round2(data.sd_nii));
      setThresholds(data.thresholds);
      setStep1Stats({
        mu_x: data.mean_nii,
        sd_x: data.std_nii,
        mu_y: data.mean_area,
        sd_y: data.std_area,
      });
      setStep1GraphLimits(data.graph_limits);
      setStep1Ready(true);

      // If datasets exist, build step2 immediately
      if (datasets.length > 0) {
        if (!requireNmaAxes()) return;
        const payload = {
          params: { datasets },
          include_sample: true,
          include_all_datasets: true,
          sd_nii: data.sd_nii,
          sd_area: data.sd_area,
          thresholds: data.thresholds,
        };
        const figRes = await callApi("/nma/settings/figure", payload);
        const traces = (figRes.figure?.data || []).filter(
          (t) => t?.mode?.includes("markers") || t?.type === "scattergl"
        );
        const stats = {
          mu_x: data.mean_nii,
          sd_x: data.std_nii,
          mu_y: data.mean_area,
          sd_y: data.std_area,
        };
        const graphLimits = figRes.graph_limits || data.graph_limits;
        setStep2Traces(traces);
        setStep2Stats(stats);
        setStep2GraphLimits(graphLimits);
        const finalFig = buildStep2Figure(
          traces,
          stats,
          graphLimits,
          data.thresholds,
          data.sd_nii,
          data.sd_area,
          true,
          "black",
          "black"
        );
        setStep2Figure(finalFig);
        setStep2Percentages(computeQuadrantPercentages(traces, data.thresholds, stats, data.sd_area));
        setFinalMode(true);
        setDownloadReady(true);
        setShowPlotConfig(true);
        setStep(2);
      } else {
        // No datasets: show final plot with no points
        const stats = {
          mu_x: data.mean_nii,
          sd_x: data.std_nii,
          mu_y: data.mean_area,
          sd_y: data.std_area,
        };
        const graphLimits = data.graph_limits;
        const finalFig = buildStep2Figure(
          [],
          stats,
          graphLimits,
          data.thresholds,
          data.sd_nii,
          data.sd_area,
          true,
          "black",
          "black"
        );
        setStep2Figure(finalFig);
        setFinalMode(true);
        setDownloadReady(true);
        setShowPlotConfig(true);
        setStep(2);
      }

      setStatus("Settings loaded.");
      setStatusLevel("success");
    } catch (err) {
      setStatus(errorMessageFromException(err, "The settings file could not be loaded. Choose a valid forNMA settings file and try again."));
      setStatusLevel("error");
    }
  };

  const updateDotConfig = (patch) => {
    setPlotConfig((prev) => ({ ...prev, dot: { ...prev.dot, ...patch } }));
  };

  const updateHeatmapConfig = (patch) => {
    setPlotConfig((prev) => ({ ...prev, heatmap: { ...prev.heatmap, ...patch } }));
  };

  const toOptionalNumber = (value) => {
    if (value === "" || value == null) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  };

  const handlePlotAll = async () => {
    if (!requireNmaAxes()) return;
    if (!plotSavePath.trim()) {
      setStatus("Choose an output folder before plotting. This is where the generated images and result files will be saved.");
      setStatusLevel("error");
      return;
    }
    scrollToTopSmooth();
    setShowPlotProgress(true);
    setShowNmaPreviewWhilePlotting(false);
    setCurrentPlotIndex(0);
    setPlotJob({
      ...DEFAULT_PLOT_JOB,
      status: "queued",
      progress: 0,
      message: "Starting plot generation...",
      output_dir: plotSavePath.trim(),
    });
    setStatus("Starting plot generation...");
    setStatusLevel("info");

    try {
      const payload = {
        params: { datasets },
        output_dir: plotSavePath.trim(),
        kind: plotConfig.kind,
        dot: {
          column1: plotConfig.dot.column1 || null,
          column2: plotConfig.dot.column2 || null,
          hue_min: toOptionalNumber(plotConfig.dot.hue_min),
          hue_max: toOptionalNumber(plotConfig.dot.hue_max),
          size_min: toOptionalNumber(plotConfig.dot.size_min),
          size_max: toOptionalNumber(plotConfig.dot.size_max),
          sample_size: toOptionalNumber(plotConfig.dot.sample_size),
          palette: plotConfig.dot.palette || null,
          single: !!plotConfig.dot.single,
          overtime: !!plotConfig.dot.overtime,
        },
        heatmap: {
          single: !!plotConfig.heatmap.single,
          overtime: !!plotConfig.heatmap.overtime,
          jointplot: !!plotConfig.heatmap.jointplot,
          palette: plotConfig.heatmap.palette || null,
        },
      };

      const res = await callApi("/nma/plots/start", payload);
      setPlotJob({
        job_id: res.job_id,
        status: res.status || "queued",
        progress: 0,
        message: "Queued",
        files: [],
        output_dir: plotSavePath.trim(),
        error: "",
      });
    } catch (err) {
      setShowPlotProgress(false);
      setPlotJob({ ...DEFAULT_PLOT_JOB });
      setStatus(errorMessageFromException(err, "Plot generation could not start. Check the output folder and selected datasets."));
      setStatusLevel("error");
    }
  };

  useEffect(() => {
    if (!plotJob.job_id) return;
    if (plotJob.status === "completed" || plotJob.status === "failed") return;

    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/nma/plots/status/${plotJob.job_id}`);
        if (res.status === 404) {
          setPlotJob({ ...DEFAULT_PLOT_JOB });
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        setPlotJob((prev) => ({ ...prev, ...data }));
        if (data.status === "completed") {
          setStatus(data.message || "Plot generation finished. Check the preview panel and output folder for the generated image files.");
          setStatusLevel("success");
        } else if (data.status === "failed") {
          setStatus(humanizeErrorMessage(data.error || data.message, "Plot generation failed. Check that the selected CSVs, columns, and output folder are valid."));
          setStatusLevel("error");
        }
      } catch {
        // keep polling
      }
    }, 1200);

    return () => clearInterval(timer);
  }, [plotJob.job_id, plotJob.status]);

  useEffect(() => {
    if (!plotJob.files || plotJob.files.length === 0) {
      setCurrentPlotIndex(0);
      return;
    }
    // Keep focus on the most recently generated figure.
    setCurrentPlotIndex(plotJob.files.length - 1);
  }, [plotJob.files]);

  useEffect(() => {
    if (!segJob.job_id) return;
    if (["completed", "failed", "canceled"].includes(segJob.status)) return;

    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/segmentation/status/${segJob.job_id}`);
        if (res.status === 404) {
          setSegJob({ ...DEFAULT_SEG_JOB });
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        setSegJob((prev) => {
          const next = { ...prev, ...data };
          if (
            next.preview_path &&
            (
              next.preview_path !== prev.preview_path ||
              next.progress !== prev.progress ||
              next.status !== prev.status
            )
          ) {
            setSegPreviewNonce((n) => n + 1);
          }
          return next;
        });
        if (data.status === "completed") {
          setStatus(data.message || "Segmentation finished successfully. Review the preview, log, and output folder before continuing.");
          setStatusLevel("success");
        } else if (data.status === "failed") {
          setStatus(humanizeErrorMessage(data.error || data.message, "Segmentation failed. Check the image folders, channel selections, and output folder."));
          setStatusLevel("error");
        } else if (data.status === "canceled") {
          setStatus(data.message || "Segmentation canceled.");
          setStatusLevel("info");
        }
      } catch {
        // keep polling
      }
    }, 900);

    return () => clearInterval(timer);
  }, [segJob.job_id, segJob.status]);

  useEffect(() => {
    if (!regJob.job_id) return;
    if (["completed", "failed", "canceled"].includes(regJob.status)) return;

    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/registration/status/${regJob.job_id}`);
        if (res.status === 404) {
          setRegJob({ ...DEFAULT_REG_JOB });
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        setRegJob((prev) => ({ ...prev, ...data }));
        if (data.status === "completed") {
          setStatus(data.message || "Registration finished successfully. Registered images were written to the selected saving path.");
          setStatusLevel("success");
        } else if (data.status === "failed") {
          setStatus(humanizeErrorMessage(data.error || data.message, "Registration failed. Check the reference channel, moving channels, image folders, and saving path."));
          setStatusLevel("error");
        } else if (data.status === "canceled") {
          setStatus(data.message || "Registration canceled.");
          setStatusLevel("info");
        }
      } catch {
        // keep polling
      }
    }, 900);

    return () => clearInterval(timer);
  }, [regJob.job_id, regJob.status]);

  useEffect(() => {
    if (!fociJob.job_id) return;
    if (["completed", "failed", "canceled"].includes(fociJob.status)) return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/foci/status/${fociJob.job_id}`);
        if (res.status === 404) {
          setFociJob({ ...DEFAULT_FOCI_JOB });
          return;
        }
        if (!res.ok) return;
        const data = await res.json();
        setFociJob((prev) => ({ ...prev, ...data }));
        if (data.status === "completed") {
          setStatus(data.message || "Foci overlay finished successfully. Output files were written to the selected saving path.");
          setStatusLevel("success");
        } else if (data.status === "failed") {
          setStatus(humanizeErrorMessage(data.error || data.message, "Foci overlay failed. Check the Pickles folder, selected channels, actions, and saving path."));
          setStatusLevel("error");
        } else if (data.status === "canceled") {
          setStatus(data.message || "Foci overlay canceled.");
          setStatusLevel("info");
        }
      } catch {
        // keep polling
      }
    }, 900);
    return () => clearInterval(timer);
  }, [fociJob.job_id, fociJob.status]);

  useEffect(() => {
    setSegPreviewPage(0);
  }, [segJob.preview_paths, segJob.preview_index, segJob.job_id]);

  useEffect(() => {
    if (plotJob.job_id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/nma/plots/active`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data?.job?.job_id) {
          setPlotJob((prev) => ({ ...DEFAULT_PLOT_JOB, ...prev, ...data.job }));
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [plotJob.job_id]);

  useEffect(() => {
    if (segJob.job_id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/segmentation/active`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data?.job?.job_id) {
          setSegJob((prev) => ({ ...DEFAULT_SEG_JOB, ...prev, ...data.job }));
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [segJob.job_id]);

  useEffect(() => {
    if (regJob.job_id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/registration/active`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data?.job?.job_id) {
          setRegJob((prev) => ({ ...DEFAULT_REG_JOB, ...prev, ...data.job }));
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [regJob.job_id]);

  useEffect(() => {
    if (fociJob.job_id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/foci/active`);
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data?.job?.job_id) {
          setFociJob((prev) => ({ ...DEFAULT_FOCI_JOB, ...prev, ...data.job }));
        }
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [fociJob.job_id]);

  useEffect(() => () => {
    if (gatingRelayoutTimerRef.current) {
      clearTimeout(gatingRelayoutTimerRef.current);
      gatingRelayoutTimerRef.current = null;
    }
    if (nmaGateRelayoutTimerRef.current) {
      clearTimeout(nmaGateRelayoutTimerRef.current);
      nmaGateRelayoutTimerRef.current = null;
    }
  }, []);

  const handleSave = async () => {
    setStatus("Saving settings...");
    setStatusLevel("info");
    try {
      if (!step1Stats) throw new Error("Run Step 2 first.");
      const payload = {
        name: datasets.find((d) => d.is_control)?.name || "control",
        mean_nii: step1Stats.mu_x,
        std_nii: step1Stats.sd_x,
        mean_area: step1Stats.mu_y,
        std_area: step1Stats.sd_y,
        sd_nii: sdNii,
        sd_area: sdArea,
        graph_limits: step1GraphLimits || [0, 0, 0, 0],
        thresholds,
      };
      await callApi("/nma/settings/save", payload);
      setStatus("Settings saved successfully.");
      setStatusLevel("success");
    } catch (err) {
      setStatus(errorMessageFromException(err, "Settings could not be saved. Choose a folder you can write to and try again."));
      setStatusLevel("error");
    }
  };

  const parseCommaList = (txt) => String(txt || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const parseIntList = (txt) => parseCommaList(txt)
    .map((s) => Number(s))
    .filter((n) => Number.isFinite(n))
    .map((n) => Math.trunc(n));

  const handlePlotDataPreview = async () => {
    const datasets = (plotData.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setPlotDataStatusMsg("Select at least one dataset with a valid CSV path. Use Browse CSV or type the full path to a readable CSV file.", "error");
      return;
    }
    if (plotData.columnsWarning) {
      setPlotDataStatusMsg(plotData.columnsWarning, "error");
      return;
    }
    const gt = plotData.graph_type || "scatter";
    if (PLOT_TYPES_REQUIRE_XY.has(gt) && (!plotData.x || !plotData.y)) {
      setPlotDataStatusMsg("Select both X and Y columns for this plot type. Use numeric measurement columns for scatter, line, AUC, rolling average, and CPD plots.", "error");
      return;
    }
    if (!PLOT_TYPES_REQUIRE_XY.has(gt) && PLOT_TYPES_REQUIRE_Y.has(gt) && !plotData.y) {
      setPlotDataStatusMsg("Select a Y column for this plot type. Choose the measurement column you want to plot.", "error");
      return;
    }
    const effectiveGraphType = (gt === "line" && !!plotData.line_rolling) ? "rolling-average" : gt;
    if (effectiveGraphType === "rolling-average") {
      const nVal = plotData.n === "" ? null : Number(plotData.n);
      if (!Number.isFinite(nVal) || nVal <= 0) {
        setPlotDataStatusMsg("Rolling average needs a window size greater than 0. Increase n and try again.", "error");
        return;
      }
    }
    if (effectiveGraphType === "cpd") {
      const fs = parseIntList(plotData.framesText);
      if (fs.length < 2) {
        setPlotDataStatusMsg("CPD needs at least 2 frames. Increase the frame range or choose data with more time points.", "error");
        return;
      }
    }
    if ((gt === "violin" || gt === "box" || gt === "dot" || gt === "bar") && plotData.x && !(plotData.categoricalColumns || []).includes(plotData.x)) {
      setPlotDataStatusMsg("For violin, box, dot, or bar plots, X must be a category such as Condition or Treatment. Choose a categorical column, or leave X empty.", "error");
      return;
    }
    scrollToTopSmooth();
    setPlotDataStatusMsg("Generating interactive preview...", "info");
    setPlotDataLoading(true);
    try {
      const shouldUseFrames = effectiveGraphType === "cpd" || effectiveGraphType === "rolling-average" || (gt === "line" && (!plotData.x || plotData.x === "Frame"));
      const payload = {
        datasets,
        graph_type: effectiveGraphType,
        x: effectiveGraphType === "cpd" ? null : (PLOT_TYPES_SUPPORT_X.has(gt) ? (plotData.x || null) : null),
        y: effectiveGraphType === "cpd" ? null : (plotData.y || null),
        hue: effectiveGraphType === "cpd" ? null : (plotData.hue || null),
        size: effectiveGraphType === "cpd" ? null : (plotData.size || null),
        violin_box: !!plotData.violin_box,
        violin_points: !!plotData.violin_points,
        box_outliers: !!plotData.box_outliers,
        compute_auc: !!plotData.compute_auc,
        control: effectiveGraphType === "cpd" ? (String(plotData.control || "").trim() || null) : null,
        conditions: [],
        frames: shouldUseFrames ? parseIntList(plotData.framesText) : [],
        dot: !!plotData.dot,
        n: effectiveGraphType === "rolling-average" ? (plotData.n === "" ? null : Number(plotData.n)) : null,
      };
      const res = await callApi("/graphs/preview", payload);
      setPlotData((prev) => ({
        ...prev,
        figure: res.figure || null,
        columns: res.columns || prev.columns || [],
        message: res.message || "",
      }));
      if (res.columns?.length) {
        setPlotData((prev) => {
          const safe = (k) => (prev[k] && res.columns.includes(prev[k]) ? prev[k] : "");
          return { ...prev, x: safe("x"), y: safe("y"), hue: safe("hue"), size: safe("size") };
        });
      }
      setPlotDataStatusMsg(res.message || "Preview ready.", "success");
    } catch (err) {
      setPlotDataStatusMsg(errorMessageFromException(err, "Preview could not be generated. Check that the selected CSV and columns match this graph type."), "error");
    } finally {
      setPlotDataLoading(false);
    }
  };

  const handleClusteringPreview = async () => {
    const datasets = (clustering.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setClusteringStatus({ level: "error", text: "Select at least one dataset. Use Add dataset or enable an existing dataset with a readable CSV path." });
      return;
    }
    if (!(clustering.columns || []).length) {
      setClusteringStatus({ level: "error", text: "Select at least one numeric feature. Choose measurement columns that contain numbers, not labels or names." });
      return;
    }
    scrollToTopSmooth();
    setClusteringLoading(true);
    setClusteringStatus({ level: "info", text: "Running UMAP preview..." });
    try {
      const payload = {
        datasets,
        columns: clustering.columns,
        method: clustering.method || "umap",
        n_neighbors: Number(clustering.n_neighbors || 15),
        min_dist: Number(clustering.min_dist ?? 0.1),
        metric: clustering.metric || "euclidean",
        scale: !!clustering.scale,
        max_points: Number(clustering.max_points || 12000),
        color_by: clustering.use_clusters ? null : (clustering.color_by || null),
        use_clusters: !!clustering.use_clusters,
        n_clusters: clustering.use_clusters ? Number(clustering.n_clusters || 8) : null,
      };
      const res = await callApi("/clustering/umap/preview", payload);
      setClustering((prev) => ({
        ...prev,
        figure: res.figure || null,
        columnsAll: res.columns || prev.columnsAll || [],
        numericColumns: res.numeric_columns || prev.numericColumns || [],
        message: res.message || "",
      }));
      setClusteringStatus({ level: "success", text: res.message || "Preview ready." });
    } catch (err) {
      setClusteringStatus({ level: "error", text: errorMessageFromException(err, "UMAP preview failed. Check that the selected features are numeric and contain valid values.") });
    } finally {
      setClusteringLoading(false);
    }
  };

  const handleClusteringElbow = async () => {
    const datasets = (clustering.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setClusteringStatus({ level: "error", text: "Select at least one dataset. Use Add dataset or enable an existing dataset with a readable CSV path." });
      return;
    }
    if (!(clustering.columns || []).length) {
      setClusteringStatus({ level: "error", text: "Select at least one numeric feature. Choose measurement columns that contain numbers, not labels or names." });
      return;
    }
    scrollToTopSmooth();
    setClusteringElbowLoading(true);
    setClusteringStatus({ level: "info", text: "Generating elbow plot..." });
    try {
      const payload = {
        datasets,
        columns: clustering.columns,
        method: clustering.method || "umap",
        n_neighbors: Number(clustering.n_neighbors || 15),
        min_dist: Number(clustering.min_dist ?? 0.1),
        metric: clustering.metric || "euclidean",
        scale: !!clustering.scale,
        max_points: Number(clustering.max_points || 12000),
        k_min: Number(clustering.k_min || 2),
        k_max: Number(clustering.k_max || 12),
      };
      const res = await callApi("/clustering/elbow/preview", payload);
      setClustering((prev) => ({ ...prev, elbowFigure: res.figure || null }));
      setClusteringStatus({ level: "success", text: res.message || "Elbow plot ready." });
    } catch (err) {
      setClusteringStatus({ level: "error", text: errorMessageFromException(err, "Elbow plot failed. Check that the selected features are numeric and have enough valid rows.") });
    } finally {
      setClusteringElbowLoading(false);
    }
  };

  const handleStatsRun = async () => {
    const method = statsState.method || "oneway";
    const datasets = (statsState.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => String(d.path || "").trim())
      .filter(Boolean);
    if (!datasets.length) {
      setStatsStatus({ level: "error", text: "Select at least one dataset with a readable CSV path before running statistics." });
      return;
    }
    if (method === "oneway" && (!statsState.numeric_col || !statsState.group_col)) {
      setStatsStatus({ level: "error", text: "One-way analysis needs one numeric measurement column and one grouping column, such as Condition." });
      return;
    }
    if (method === "twoway" && (!statsState.numeric_col || !statsState.group_col1 || !statsState.group_col2)) {
      setStatsStatus({ level: "error", text: "Two-way analysis needs one numeric measurement column plus two grouping columns: Factor A and Factor B." });
      return;
    }
    if (method === "chi2" && (!statsState.group_col || !statsState.category_col)) {
      setStatsStatus({ level: "error", text: "Chi-square analysis needs a group column and a category column. Choose columns with labels/categories, not continuous measurements." });
      return;
    }
    if (method === "chi2-subgroups" && (!statsState.group_col || !statsState.condition_col)) {
      setStatsStatus({ level: "error", text: "Chi-square subgroups needs a group column and a condition column. Choose columns that identify the categories to compare." });
      return;
    }

    const pairs = String(statsState.pairs_text || "")
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
    const filters = (statsState.filters || [])
      .map((filter) => ({
        column: String(filter.column || "").trim(),
        values: (filter.values || []).map(normalizeFilterOption).filter(Boolean),
      }))
      .filter((filter) => filter.column);
    if (filters.some((filter) => filter.values.length === 0)) {
      setStatsStatus({ level: "error", text: "Each active subset filter needs at least one selected value. Pick values for the filter or turn that filter off." });
      return;
    }

    scrollToTopSmooth();
    setStatsLoading(true);
    setStatsStatus({ level: "info", text: "Running statistical analysis..." });
    try {
      const payload = {
        paths: datasets,
        method,
        numeric_col: statsState.numeric_col || null,
        group_col: statsState.group_col || null,
        group_col1: statsState.group_col1 || null,
        group_col2: statsState.group_col2 || null,
        category_col: statsState.category_col || null,
        condition_col: statsState.condition_col || null,
        alpha: Number(statsState.alpha || 0.05),
        expected_min: Number(statsState.expected_min || 5.0),
        correction_method: statsState.correction_method || "auto",
        pairs_of_interest: pairs,
        filters,
      };
      const res = await callApi("/stats/run", payload);
      setStatsState((prev) => ({
        ...prev,
        tables: res.tables || [],
        log: res.log || "",
        message: res.message || "",
      }));
      setStatsStatus({ level: "success", text: res.message || "Analysis complete." });
    } catch (err) {
      setStatsStatus({ level: "error", text: errorMessageFromException(err, "The statistical analysis could not run. Check that the selected columns match the analysis type and contain enough valid data.") });
    } finally {
      setStatsLoading(false);
    }
  };

  const parseOptNumber = (v) => {
    if (v === "" || v == null) return null;
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  };

  const handleGatingPreview = async ({ overrideBounds = null, fromDrag = false, resetBounds = false } = {}) => {
    const datasets = (gatingState.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
        pkl_dir: String(d.pkl_dir || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setGatingStatus({ level: "error", text: "Select at least one dataset with a readable CSV path before previewing a gate." });
      return;
    }
    if (!gatingState.x_col || !gatingState.y_col) {
      setGatingStatus({ level: "error", text: "Select both X and Y columns. Choose numeric measurement columns to define the gate axes." });
      return;
    }
    if (!fromDrag) {
      scrollToTopSmooth();
    }
    setGatingLoading(true);
    setGatingStatus({ level: "info", text: fromDrag ? "Updating gate preview..." : "Generating gating preview..." });
    const requestId = gatingPreviewRequestRef.current + 1;
    gatingPreviewRequestRef.current = requestId;
    try {
      const readBound = (key) => {
        if (resetBounds) return null;
        if (overrideBounds && Object.prototype.hasOwnProperty.call(overrideBounds, key)) {
          return overrideBounds[key];
        }
        return parseOptNumber(gatingState[key]);
      };
      const payload = {
        datasets,
        x_col: gatingState.x_col,
        y_col: gatingState.y_col,
        x_min: readBound("x_min"),
        x_max: readBound("x_max"),
        y_min: readBound("y_min"),
        y_max: readBound("y_max"),
        q_low: Number(gatingState.q_low ?? 0.05),
        q_high: Number(gatingState.q_high ?? 0.95),
        max_points: Number(gatingState.max_points || 12000),
        color_by_dataset: true,
      };
      const res = await callApi("/filters/preview", payload);
      if (requestId !== gatingPreviewRequestRef.current) return;
      setGatingState((prev) => ({
        ...prev,
        figure: res.figure || null,
        tables: res.tables || [],
        message: res.message || "",
        x_min: String(res.bounds?.x_min ?? prev.x_min ?? ""),
        x_max: String(res.bounds?.x_max ?? prev.x_max ?? ""),
        y_min: String(res.bounds?.y_min ?? prev.y_min ?? ""),
        y_max: String(res.bounds?.y_max ?? prev.y_max ?? ""),
      }));
      setGatingStatus({ level: "success", text: res.message || "Preview ready." });
    } catch (err) {
      if (requestId !== gatingPreviewRequestRef.current) return;
      setGatingStatus({ level: "error", text: errorMessageFromException(err, "Gating preview failed. Check that X and Y are numeric columns with valid rows.") });
    } finally {
      if (requestId === gatingPreviewRequestRef.current) {
        setGatingLoading(false);
      }
    }
  };

  const handleGatingApply = async () => {
    const datasets = (gatingState.datasets || [])
      .filter((d) => d.enabled !== false)
      .map((d) => ({
        name: String(d.name || "").trim(),
        path: String(d.path || "").trim(),
        pkl_dir: String(d.pkl_dir || "").trim(),
      }))
      .filter((d) => d.path);
    if (!datasets.length) {
      setGatingStatus({ level: "error", text: "Select at least one dataset with a readable CSV path before applying a gate." });
      return;
    }
    if (!gatingState.x_col || !gatingState.y_col) {
      setGatingStatus({ level: "error", text: "Select both X and Y columns. Choose numeric measurement columns to define the gate axes." });
      return;
    }
    if (!String(gatingState.output_dir || "").trim()) {
      setGatingStatus({ level: "error", text: "Choose an output directory to save gated CSVs. Use a folder where you have write permission." });
      return;
    }
    if (gatingState.draw_images && datasets.some((d) => !d.pkl_dir)) {
      setGatingStatus({ level: "error", text: "Choose a PKL folder for every active dataset before applying the gate to images. Each PKL folder must match its dataset." });
      return;
    }
    scrollToTopSmooth();
    setGatingApplying(true);
    setGatingStatus({ level: "info", text: "Applying gate and writing files..." });
    try {
      const payload = {
        datasets,
        x_col: gatingState.x_col,
        y_col: gatingState.y_col,
        x_min: parseOptNumber(gatingState.x_min),
        x_max: parseOptNumber(gatingState.x_max),
        y_min: parseOptNumber(gatingState.y_min),
        y_max: parseOptNumber(gatingState.y_max),
        q_low: Number(gatingState.q_low ?? 0.05),
        q_high: Number(gatingState.q_high ?? 0.95),
        max_points: Number(gatingState.max_points || 12000),
        color_by_dataset: !!gatingState.color_by_dataset,
        output_dir: String(gatingState.output_dir || "").trim(),
        draw_images: !!gatingState.draw_images,
      };
      const res = await callApi("/filters/apply", payload);
      setGatingState((prev) => ({
        ...prev,
        tables: res.tables || prev.tables || [],
        files: res.files || [],
        message: res.message || "",
        output_dir: res.output_dir || prev.output_dir || "",
        x_min: String(res.bounds?.x_min ?? prev.x_min ?? ""),
        x_max: String(res.bounds?.x_max ?? prev.x_max ?? ""),
        y_min: String(res.bounds?.y_min ?? prev.y_min ?? ""),
        y_max: String(res.bounds?.y_max ?? prev.y_max ?? ""),
      }));
      setGatingStatus({ level: "success", text: res.message || "Gating complete." });
    } catch (err) {
      setGatingStatus({ level: "error", text: errorMessageFromException(err, "The gate could not be applied. Check the output folder, PKL folders, and selected numeric columns.") });
    } finally {
      setGatingApplying(false);
    }
  };

  const handleGatingRelayout = (evt) => {
    if (!evt) return;
    const shape0 = evt["shapes[0]"];
    const pick = (keyA, keyB, fallback) => {
      const a = evt[keyA];
      const b = evt[keyB];
      if (a != null) return a;
      if (b != null) return b;
      return fallback;
    };
    const nextX0 = shape0?.x0 ?? pick("shapes[0].x0", "shapes[0].x1", null);
    const nextX1 = shape0?.x1 ?? pick("shapes[0].x1", "shapes[0].x0", null);
    const nextY0 = shape0?.y0 ?? pick("shapes[0].y0", "shapes[0].y1", null);
    const nextY1 = shape0?.y1 ?? pick("shapes[0].y1", "shapes[0].y0", null);
    if (nextX0 == null || nextX1 == null || nextY0 == null || nextY1 == null) return;

    const xMin = Math.min(Number(nextX0), Number(nextX1));
    const xMax = Math.max(Number(nextX0), Number(nextX1));
    const yMin = Math.min(Number(nextY0), Number(nextY1));
    const yMax = Math.max(Number(nextY0), Number(nextY1));
    if (![xMin, xMax, yMin, yMax].every((n) => Number.isFinite(n))) return;

    const prevXMin = Number(gatingState.x_min);
    const prevXMax = Number(gatingState.x_max);
    const prevYMin = Number(gatingState.y_min);
    const prevYMax = Number(gatingState.y_max);
    if (
      Number.isFinite(prevXMin) && Number.isFinite(prevXMax) && Number.isFinite(prevYMin) && Number.isFinite(prevYMax) &&
      Math.abs(prevXMin - xMin) < 1e-9 &&
      Math.abs(prevXMax - xMax) < 1e-9 &&
      Math.abs(prevYMin - yMin) < 1e-9 &&
      Math.abs(prevYMax - yMax) < 1e-9
    ) return;

    setGatingState((prev) => ({
      ...prev,
      x_min: String(xMin),
      x_max: String(xMax),
      y_min: String(yMin),
      y_max: String(yMax),
    }));
    if (gatingRelayoutTimerRef.current) {
      clearTimeout(gatingRelayoutTimerRef.current);
      gatingRelayoutTimerRef.current = null;
    }
    gatingRelayoutTimerRef.current = setTimeout(() => {
      handleGatingPreview({
        overrideBounds: { x_min: xMin, x_max: xMax, y_min: yMin, y_max: yMax },
        fromDrag: true,
      });
    }, 220);
  };

  const trackingFramePayload = (override = {}) => ({
    table_path: String((override.table_path ?? trackingState.table_path) || "").trim(),
    frame: Number(override.frame ?? trackingState.frame ?? 0),
    image_dir: String((override.image_dir ?? trackingState.image_dir) || "").trim() || null,
    image_col: (override.image_col ?? trackingState.image_col) || null,
    preview_cache_dir: String((override.preview_cache_dir ?? trackingState.preview_cache_dir) || "").trim() || null,
    trail_window: Number(override.trail_window ?? trackingState.trail_window ?? 7),
    show_complete_trail: !!(override.show_complete_trail ?? trackingState.show_complete_trail),
  });

  const applyTrackingPreviewResponse = (res) => {
    setTrackingState((prev) => ({
      ...prev,
      table_path: res.table_path || prev.table_path,
      image_col: res.image_col || prev.image_col,
      preview_cache_dir: res.preview_cache_dir || prev.preview_cache_dir || "",
      preview_image_path: res.preview_image_path || "",
      preview_nonce: Number(prev.preview_nonce || 0) + 1,
      frame: Number(res.frame ?? prev.frame ?? 0),
      max_frame: Number(res.max_frame ?? prev.max_frame ?? 0),
      figure: res.figure || null,
      total_rows: Number(res.total_rows ?? prev.total_rows ?? 0),
      total_tracks: Number(res.total_tracks ?? prev.total_tracks ?? 0),
      message: res.message || "",
    }));
  };

  const createTrackingUndoCheckpoint = async () => {
    const tablePath = String(trackingState.table_path || "").trim();
    if (!tablePath) {
      throw new Error("Run automatic tracking first.");
    }
    const res = await callApi("/tracking/checkpoint/create", { table_path: tablePath });
    return String(res.checkpoint_path || "").trim();
  };

  const handleTrackingRunAutomatic = async () => {
    if (!String(trackingState.path_to_table || "").trim()) {
      setTrackingStatus({ level: "error", text: "Select the input Results.csv table. This table should contain the segmentation results for the images you want to track." });
      return;
    }
    if (!String(trackingState.image_dir || "").trim()) {
      setTrackingStatus({ level: "error", text: "Select the image folder. It must contain the images referenced by the Results.csv table." });
      return;
    }
    if (!String(trackingState.image_col || "").trim()) {
      setTrackingStatus({ level: "error", text: "Select the CSV column that contains image file names, such as Image_name_channel. The tracker uses it to match table rows to images." });
      return;
    }
    scrollToTopSmooth();
    setTrackingRunning(true);
    setTrackingStatus({ level: "info", text: "Running automatic tracking..." });
    try {
      const payload = {
        path_to_table: String(trackingState.path_to_table || "").trim(),
        image_dir: String(trackingState.image_dir || "").trim(),
        image_col: trackingState.image_col || "",
        max_distance: Number(trackingState.max_distance || 30),
        time_window: Number(trackingState.time_window || 5),
        max_split_distance: Number(trackingState.max_split_distance || 10),
        max_gap_closing_distance: Number(trackingState.max_gap_closing_distance || 30),
      };
      const res = await callApi("/tracking/run", payload);
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({ ...prev, selected: [] }));
      setTrackingStatus({ level: "success", text: res.message || "Automatic tracking complete." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "Automatic tracking could not run. Check the Results.csv table, image folder, and image-name column.") });
    } finally {
      setTrackingRunning(false);
    }
  };

  const handleTrackingGoToCorrection = () => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first. The correction tools need an initial tracked table before they can open." });
      return;
    }
    setTrackingState((prev) => ({ ...prev, workflow_stage: "menu" }));
    setTrackingStatus({ level: "info", text: "Choose the next action: save results or correct tracks." });
  };

  const handleTrackingOpenCorrection = () => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first. Saving requires tracking results to exist." });
      return;
    }
    setTrackingState((prev) => ({ ...prev, workflow_stage: "correction" }));
    setTrackingStatus({ level: "info", text: "Manual correction enabled." });
  };

  const handleTrackingSaveResults = async (includeImages = true) => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first. There is no tracked table to save yet." });
      return;
    }
    if (!String(trackingState.save_results_dir || "").trim()) {
      setTrackingStatus({ level: "error", text: "Select a destination folder to save results. Use a folder where you have write permission." });
      return;
    }
    setTrackingLoadingFrame(true);
    setTrackingStatus({ level: "info", text: "Saving tracking results..." });
    try {
      const res = await callApi("/tracking/save-results", {
        table_path: String(trackingState.table_path || "").trim(),
        output_dir: String(trackingState.save_results_dir || "").trim(),
        preview_cache_dir: String(trackingState.preview_cache_dir || "").trim() || null,
        include_images: !!includeImages,
      });
      setTrackingStatus({ level: "success", text: res.message || "Results saved." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "Tracking results could not be saved. Choose a destination folder you can write to and try again.") });
    } finally {
      setTrackingLoadingFrame(false);
    }
  };

  const handleTrackingUndo = async () => {
    const checkpointPath = String(trackingState.undo_checkpoint_path || "").trim();
    if (!checkpointPath) {
      setTrackingStatus({ level: "error", text: "No undo checkpoint is available yet. Make an edit first, then Undo will become available." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Undoing last tracking action..." });
    try {
      const res = await callApi("/tracking/checkpoint/restore", {
        ...trackingFramePayload(),
        checkpoint_path: checkpointPath,
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({
        ...prev,
        selected: [],
        selected_markers: [],
        undo_checkpoint_path: "",
      }));
      setTrackingStatus({ level: "success", text: res.message || "Last action undone." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "Undo failed. There may be no saved checkpoint for the last edit.") });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingSaveProgress = async () => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first. Progress can only be saved after a tracked table exists." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Saving tracking progress..." });
    try {
      const res = await callApi("/tracking/progress/save", trackingFramePayload());
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({
        ...prev,
        table_path: res.saved_table_path || prev.table_path,
        saved_progress_path: res.saved_table_path || prev.saved_progress_path,
      }));
      setTrackingStatus({ level: "success", text: res.message || "Progress saved." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "Progress could not be saved. Choose a writable folder and try again.") });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingRefreshFrame = async (override = {}) => {
    if (!String(trackingState.table_path || "").trim()) {
      setTrackingStatus({ level: "error", text: "Run automatic tracking first or provide a tracked table. The preview needs tracking results to show." });
      return;
    }
    setTrackingLoadingFrame(true);
    setTrackingStatus({ level: "info", text: "Updating tracking preview..." });
    try {
      const res = await callApi("/tracking/preview", trackingFramePayload(override));
      applyTrackingPreviewResponse(res);
      setTrackingStatus({ level: "success", text: res.message || "Preview updated." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "Tracking preview failed. Check that the tracked table and image folder still match.") });
    } finally {
      setTrackingLoadingFrame(false);
    }
  };

  const handleTrackingStepFrame = async (delta) => {
    const current = Number(trackingState.frame || 0);
    const maxFrame = Number(trackingState.max_frame || 0);
    const target = Math.max(0, Math.min(maxFrame, current + delta));
    if (target === current) return;
    const cacheDir = String(trackingState.preview_cache_dir || "").trim();
    if (cacheDir) {
      const frameName = String(target).padStart(5, "0");
      const pngPath = `${cacheDir}/${frameName}.png`;
      setTrackingState((prev) => ({
        ...prev,
        frame: target,
        preview_image_path: pngPath,
      }));
      return;
    }
    setTrackingState((prev) => ({ ...prev, frame: target }));
    await handleTrackingRefreshFrame({ frame: target });
  };

  const handleTrackingViewerClick = async (evt) => {
    if (String(trackingState.workflow_stage || "step1") !== "correction") return;
    if (!String(trackingState.table_path || "").trim()) return;
    const imgEl = evt?.currentTarget;
    if (!imgEl) return;
    const rect = imgEl.getBoundingClientRect();
    const rx = (evt.clientX - rect.left) / Math.max(1, rect.width);
    const ry = (evt.clientY - rect.top) / Math.max(1, rect.height);
    const naturalW = Number(imgEl.naturalWidth || trackingState.viewer_w || 0);
    const naturalH = Number(imgEl.naturalHeight || trackingState.viewer_h || 0);
    const x = rx * naturalW;
    const y = ry * naturalH;
    if (!Number.isFinite(x) || !Number.isFinite(y)) return;
    try {
      const res = await callApi("/tracking/select-point", {
        ...trackingFramePayload(),
        x,
        y,
        max_distance: 35,
      });
      const picked = res.selection;
      setTrackingState((prev) => {
        const already = (prev.selected || []).some(
          (s) => s.frame === picked.frame && s.cell === picked.cell && s.track_id === picked.track_id
        );
        if (already) return prev;
        const nextSelected = [...(prev.selected || []), picked];
        const nextMarkers = [...(prev.selected_markers || []), { frame: Number(picked.frame), x: Number(res.x), y: Number(res.y) }];
        return { ...prev, selected: nextSelected, selected_markers: nextMarkers };
      });
      setTrackingStatus({ level: "success", text: res.message || "Track selected." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "No track was found at the clicked position. Click closer to a visible cell marker and try again.") });
    }
  };

  const handleTrackingDelete = async () => {
    if (!(trackingState.selected || []).length) {
      setTrackingStatus({ level: "error", text: "Select at least one point or track first. Click a visible cell marker before deleting." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Deleting selected tracks..." });
    try {
      const undoCheckpointPath = await createTrackingUndoCheckpoint();
      const res = await callApi("/tracking/edit/delete", {
        ...trackingFramePayload(),
        selections: trackingState.selected || [],
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({ ...prev, selected: [], selected_markers: [], undo_checkpoint_path: undoCheckpointPath }));
      setTrackingStatus({ level: "success", text: res.message || "Tracks deleted." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "The selected tracks could not be deleted. Select one or more visible tracks and try again.") });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingLink = async () => {
    if ((trackingState.selected || []).length < 2) {
      setTrackingStatus({ level: "error", text: "Select at least two points to link tracks. Click the cells that should belong to the same track, then try again." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Linking selected tracks..." });
    try {
      const undoCheckpointPath = await createTrackingUndoCheckpoint();
      const targetFrame = Math.max(...(trackingState.selected || []).map((s) => Number(s.frame || 0)));
      const res = await callApi("/tracking/edit/link", {
        ...trackingFramePayload({ frame: targetFrame }),
        selections: trackingState.selected || [],
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({
        ...prev,
        selected: [],
        selected_markers: [],
        undo_checkpoint_path: undoCheckpointPath,
      }));
      setTrackingStatus({ level: "success", text: res.message || "Tracks linked." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "The selected tracks could not be linked. Select at least two points from the tracks you want to connect.") });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingDivision = async () => {
    if ((trackingState.selected || []).length !== 3) {
      setTrackingStatus({ level: "error", text: "Select exactly 3 cells: one mother cell and two daughter cells. The mother must be from an earlier frame." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Applying cell division..." });
    try {
      const undoCheckpointPath = await createTrackingUndoCheckpoint();
      const targetFrame = Math.max(...(trackingState.selected || []).map((s) => Number(s.frame || 0)));
      const res = await callApi("/tracking/edit/division", {
        ...trackingFramePayload({ frame: targetFrame }),
        selections: trackingState.selected || [],
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({
        ...prev,
        selected: [],
        selected_markers: [],
        undo_checkpoint_path: undoCheckpointPath,
      }));
      setTrackingStatus({ level: "success", text: res.message || "Cell division linked." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "Cell division could not be linked. Select exactly one mother cell and two daughter cells in the expected frames.") });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleTrackingUnlink = async () => {
    if (!(trackingState.selected || []).length) {
      setTrackingStatus({ level: "error", text: "Select one or more linked cells first. Click the cells you want to unlink, then try again." });
      return;
    }
    setTrackingEditing(true);
    setTrackingStatus({ level: "info", text: "Unlinking selected cells..." });
    try {
      const undoCheckpointPath = await createTrackingUndoCheckpoint();
      const targetFrame = Math.max(...(trackingState.selected || []).map((s) => Number(s.frame || 0)));
      const res = await callApi("/tracking/edit/unlink", {
        ...trackingFramePayload({ frame: targetFrame }),
        selections: trackingState.selected || [],
      });
      applyTrackingPreviewResponse(res);
      setTrackingState((prev) => ({ ...prev, selected: [], selected_markers: [], undo_checkpoint_path: undoCheckpointPath }));
      setTrackingStatus({ level: "success", text: res.message || "Selected cells unlinked." });
    } catch (err) {
      setTrackingStatus({ level: "error", text: errorMessageFromException(err, "The selected cells could not be unlinked. Select one or more linked cells and try again.") });
    } finally {
      setTrackingEditing(false);
    }
  };

  const handleResetNma = () => {
    const ok = window.confirm("Reset NMA settings and return to initial state?");
    if (!ok) return;
    setRows(initialNmaRows());
    setCollapsedById({});
    setStep(0);
    setControlGateReady(false);
    setControlGateSd("2");
    setControlGateBounds({ x_min: "", x_max: "", y_min: "", y_max: "" });
    setControlGateMeta(null);
    setControlGateFigure(null);
    setStep1Ready(false);
    setStatus("");
    setStatusLevel("info");
    setStep1Figure(null);
    setStep1Stats(null);
    setStep1GraphLimits(null);
    setStep1Sample(null);
    setSdArea(1.0);
    setSdNii(1.0);
    setThresholds({
      v_up: 0,
      v_mid: 0,
      v_down: 0,
      v_down2: 0,
      y_high: 0,
      y_low: 0,
    });
    setStep2Figure(null);
    setStep2Traces(null);
    setStep2Stats(null);
    setStep2GraphLimits(null);
    setFinalMode(false);
    setDownloadReady(false);
    setStep2Percentages(null);
    setShowPlotConfig(false);
    setPlotConfig(initialPlotConfig());
    setPlotSavePath("");
    setPlotJob({ ...DEFAULT_PLOT_JOB });
    setCurrentPlotIndex(0);
    setShowNmaPreviewWhilePlotting(false);
    setShowPlotProgress(false);
    attemptedColumnsRef.current = new Set();
  };

  const handleResetRegistrationUi = () => {
    if (["starting", "queued", "running", "canceling"].includes(regJob.status || "idle")) return;
    const ok = window.confirm("Reset Image Registration screen to a clean state?");
    if (!ok) return;
    setRegJob({ ...DEFAULT_REG_JOB });
    setRegPanelResetKey((k) => k + 1);
    setStatus("");
    setStatusLevel("info");
  };

  const handleResetFociUi = () => {
    if (["starting", "queued", "running", "canceling"].includes(fociJob.status || "idle")) return;
    const ok = window.confirm("Reset Foci Overlay screen to a clean state?");
    if (!ok) return;
    setFociJob({ ...DEFAULT_FOCI_JOB });
    setFociPanelResetKey((k) => k + 1);
    setStatus("");
    setStatusLevel("info");
  };

  const handleResetPlotDataUi = () => {
    if (plotDataLoading) return;
    const ok = window.confirm("Reset Plot Data screen to a clean state?");
    if (!ok) return;
    setPlotData(initialPlotDataState());
    setPlotDataStatus({ level: "info", text: "" });
    setPlotDataLoading(false);
    plotDataColsCacheRef.current = {};
  };

  const handleResetClusteringUi = () => {
    if (clusteringLoading || clusteringElbowLoading) return;
    const ok = window.confirm("Reset Clustering screen to a clean state?");
    if (!ok) return;
    setClustering(initialClusteringState());
    setClusteringStatus({ level: "info", text: "" });
    setClusteringLoading(false);
    setClusteringElbowLoading(false);
    clusteringColsCacheRef.current = {};
  };

  const handleResetStatisticsUi = () => {
    if (statsLoading) return;
    const ok = window.confirm("Reset Statistics screen to a clean state?");
    if (!ok) return;
    setStatsState(initialStatsState());
    setStatsStatus({ level: "info", text: "" });
    setStatsLoading(false);
    statsColsCacheRef.current = {};
    statsFilterValuesCacheRef.current = {};
  };

  const handleResetGatingUi = () => {
    if (gatingLoading || gatingApplying) return;
    const ok = window.confirm("Reset Gating screen to a clean state?");
    if (!ok) return;
    setGatingState(initialGatingState());
    setGatingStatus({ level: "info", text: "" });
    setGatingLoading(false);
    setGatingApplying(false);
    gatingColsCacheRef.current = {};
  };

  const handleResetTrackingUi = () => {
    if (trackingRunning || trackingLoadingFrame || trackingEditing) return;
    const ok = window.confirm("Reset Tracking screen to a clean state?");
    if (!ok) return;
    setTrackingState(initialTrackingState());
    setTrackingStatus({ level: "info", text: "" });
    setTrackingRunning(false);
    setTrackingLoadingFrame(false);
    setTrackingEditing(false);
  };

  const updateNmaAreaSd = (value) => {
    const v = round2(value);
    setSdArea(v);
    if (step1Stats && step1GraphLimits && step1Sample) {
      setStep1Figure(buildStep1Figure(step1Sample, step1Stats, step1GraphLimits, sdNii, v));
      setThresholds(computeThresholds(step1Stats, sdNii, v));
    }
  };

  const updateNmaNiiSd = (value) => {
    const v = round2(value);
    setSdNii(v);
    if (step1Stats && step1GraphLimits && step1Sample) {
      setStep1Figure(buildStep1Figure(step1Sample, step1Stats, step1GraphLimits, v, sdArea));
      setThresholds(computeThresholds(step1Stats, v, sdArea));
    }
  };

  const focusNmaPlotConfig = (level = "info") => {
    setAllCollapsed(true);
    setShowPlotConfig(true);
    setShowPlotProgress(false);
    setHighlightPlotConfig(true);
    setStatus("Settings are ready. Choose plot style, saving path, and output options in the left panel.");
    setStatusLevel(level);
    window.setTimeout(() => {
      const target = document.querySelector(".nma-plot-config");
      if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
    window.setTimeout(() => setHighlightPlotConfig(false), 1800);
  };

  const renderNmaStepControls = () => {
    if (!(controlGateReady || step1Ready)) return null;
    if (finalMode && downloadReady) {
      return (
        <div className="workflow-bar workflow-bar-done">
          <div className="workflow-done-message">
            <div className="status-icon">OK</div>
            <div className="status-body">
              <strong>Success</strong>
              <span>Your NMA settings were created successfully. Use the left panel to choose plot style, saving path, and output options.</span>
            </div>
          </div>
          <div className="wizard-actions">
            <Button
              className="primary"
              onClick={() => {
                window.location.href = `${API_BASE}/nma/settings/download`;
              }}
            >
              Download settings
            </Button>
            <Button
              className="secondary"
              onClick={() => focusNmaPlotConfig()}
            >
              Configure plots
            </Button>
          </div>
        </div>
      );
    }
    if (showPlotConfig) return null;
    return (
      <div className="workflow-bar">
        <div className="stepper">
          <div className={`chip ${step === 0 ? "active" : ""}`}>Step 1</div>
          <div className={`chip ${step === 1 ? "active" : ""}`}>Step 2</div>
          <div className={`chip ${step === 2 ? "active" : ""}`}>Step 3</div>
        </div>
        <div className="wizard-actions">
          {step1Ready && (
            <Button
              className="secondary"
              onClick={() => setStep(step === 2 ? 1 : 0)}
              disabled={step === 0 || (step === 1 && !controlGateReady)}
            >
              Previous
            </Button>
          )}
          {!step1Ready ? (
            <Button className="primary" onClick={handleStep1} disabled={!controlGateReady}>Use gate for Step 2</Button>
          ) : step === 1 ? (
            <Button
              className="primary"
              onClick={async () => {
                const ok = await handleStep2();
                if (ok) setStep(2);
              }}
            >
              Next
            </Button>
          ) : step === 0 ? (
            <Button className="primary" onClick={handleStep1} disabled={!controlGateReady}>Use gate for Step 2</Button>
          ) : (
            <Button className="primary" onClick={handleComplete}>Complete</Button>
          )}
        </div>
      </div>
    );
  };

  const handleResetActiveModule = () => {
    if (activeModule === "Home") {
      setHomeSection("about");
    } else if (activeModule === "Image Registration") {
      handleResetRegistrationUi();
    } else if (activeModule === "Segmentation") {
      handleResetSegmentationUi();
    } else if (activeModule === "Gating") {
      handleResetGatingUi();
    } else if (activeModule === "Foci Overlay") {
      handleResetFociUi();
    } else if (activeModule === "NMA") {
      handleResetNma();
    } else if (activeModule === "Plot Data") {
      handleResetPlotDataUi();
    } else if (activeModule === "Clustering") {
      handleResetClusteringUi();
    } else if (activeModule === "Statistics") {
      handleResetStatisticsUi();
    } else if (activeModule === "Tracking") {
      handleResetTrackingUi();
    }
  };

  const resetActiveDisabled =
    (activeModule === "Image Registration" && ["starting", "queued", "running", "canceling"].includes(regJob.status || "idle")) ||
    (activeModule === "Segmentation" && ["starting", "queued", "running", "canceling"].includes(segJob.status || "idle")) ||
    (activeModule === "Foci Overlay" && ["starting", "queued", "running", "canceling"].includes(fociJob.status || "idle")) ||
    (activeModule === "Gating" && (gatingLoading || gatingApplying)) ||
    (activeModule === "Plot Data" && plotDataLoading) ||
    (activeModule === "Clustering" && (clusteringLoading || clusteringElbowLoading)) ||
    (activeModule === "Statistics" && statsLoading) ||
    (activeModule === "Tracking" && (trackingRunning || trackingLoadingFrame || trackingEditing));

  return (
    <div className="app">
      <div className="top-shell">
        <nav className="module-menu" aria-label="forNMA stages">
          <div className="topbar-brand">
            <div className="topbar-logo-slot" aria-hidden="true">
              <span className="topbar-logo-mark">FN</span>
            </div>
            <div>
              <div className="logo">forNMA</div>
            </div>
          </div>
          <div className="module-menu-list">
            {FORNMA_STAGES.map((stage) => (
              <Button
                key={stage}
                type="button"
                className={`module-chip ${stage === activeModule ? "active" : ""}`}
                data-state={stage === activeModule ? "active" : "inactive"}
                onClick={() => {
                  setActiveModule(stage);
                }}
              >
                <span className="module-chip-label">{stage}</span>
              </Button>
            ))}
          </div>
          <div className="top-actions" aria-label="Current module actions">
            {activeModule !== "Home" && (
              <Button type="button" className="top-action" onClick={() => handleOpenTutorial(activeModule)}>
                <span className="top-action-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" focusable="false">
                    <path d="M4 5.5c0-.83.67-1.5 1.5-1.5H10c1.1 0 2 .9 2 2v14c0-1.1-.9-2-2-2H5.5C4.67 18 4 17.33 4 16.5v-11Z" />
                    <path d="M20 5.5c0-.83-.67-1.5-1.5-1.5H14c-1.1 0-2 .9-2 2v14c0-1.1.9-2 2-2h4.5c.83 0 1.5-.67 1.5-1.5v-11Z" />
                  </svg>
                </span>
                <span>Tutorial</span>
              </Button>
            )}
            <Button type="button" className="top-action" onClick={handleResetActiveModule} disabled={resetActiveDisabled}>
              <span className="top-action-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" focusable="false">
                  <path d="M20 12a8 8 0 1 1-2.34-5.66" />
                  <path d="M20 4v5h-5" />
                </svg>
              </span>
              <span>Reset</span>
            </Button>
          </div>
        </nav>
      </div>

      <div className="layout">
        {activeModule === "Home" ? (
          <>
            <HomeLeftPanel activeSection={homeSection} onSelectSection={handleSelectHomeSection} />
            <main className="content home-content" ref={homeScrollRef}>
              <section className="home-stack">
                <div id="home-about" className="section home-section-card">
                  <div className="home-hero">
                    <div className="home-logo-box">forNMA</div>
                    <div>
                      <h2>About forNMA</h2>
                      <p className="hint hint-muted">
                        forNMA is a modular microscopy analysis environment that brings registration, segmentation,
                        gating, foci inspection, NMA workflows, plotting, clustering, statistics, and tracking into a
                        single interface. Each tab can be used as part of a full workflow or on its own, depending on
                        the question you want to answer.
                      </p>
                    </div>
                  </div>
                  <div className="home-meta-grid">
                    <div className="home-info-card">
                      <h4>How to read the interface</h4>
                      <ul className="home-bullet-list compact">
                        {HOME_INTERFACE_TIPS.slice(0, 3).map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="home-info-card">
                      <h4>Running analyses</h4>
                      <ul className="home-bullet-list compact">
                        {HOME_INTERFACE_TIPS.slice(3).map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="home-info-card">
                      <h4>Practical recommendation</h4>
                      <p className="hint hint-muted">
                        Start with the module that matches your immediate goal. Segmentation and NMA are common entry
                        points, while registration and tracking depend more directly on how the images were acquired.
                      </p>
                    </div>
                  </div>
                </div>

                <div id="home-article" className="section home-section-card">
                  <h3>Article</h3>
                  <p className="hint hint-muted">
                    The full scientific rationale for each module should be described in the article or thesis that
                    accompanies the software. Use that material for methodological details, validation strategy, and
                    citation guidance.
                  </p>
                </div>

                {HOME_MODULE_GUIDES.map((section) => (
                  <div key={section.id} id={`home-${section.id}`} className="section home-section-card">
                    <HomeTutorialSection {...section} />
                  </div>
                ))}

                <div id="home-resources" className="section home-section-card">
                  <h3>Resources</h3>
                  <ul className="home-bullet-list">
                    {HOME_RESOURCES.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              </section>
            </main>
          </>
        ) : activeModule === "Segmentation" ? (
          <>
            <SegmentationLeftPanel
              key={`seg-panel-${segPanelResetKey}`}
              onPickDirectory={async () => {
                try {
                  const res = await pickDirectoryPath();
                  return res.path || "";
                } catch {
                  return "";
                }
              }}
              onStartSegmentation={handleStartSegmentation}
              onStopSegmentation={handleStopSegmentation}
              onResetSegmentation={handleResetSegmentationUi}
              segJob={segJob}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Segmentation")}>
                    Tutorial
                  </button>
                  <button
                    className="ghost btn-small"
                    onClick={handleResetSegmentationUi}
                    disabled={["starting", "queued", "running", "canceling"].includes(segJob.status || "idle")}
                  >
                    Reset
                  </button>
                </div>
                {hasSegSession ? (
                  <div className="section tracking-viewer-section">
                    <h3>Execution progress</h3>
                    <div className="progress-wrap">
                      <div
                        className={`progress-fill ${segJob.status === "starting" || segJob.status === "running" || segJob.status === "queued" || segJob.status === "canceling" ? "running" : ""}`}
                        style={{ width: `${Math.max(0, Math.min(100, segJob.progress || 0))}%` }}
                      />
                    </div>
                    <Status
                      level={segJob.status === "completed" ? "success" : segJob.status === "failed" ? "error" : "info"}
                      text={segJob.message || "Waiting to start."}
                    />
                    {segJob.error && <Status level="error" text={segJob.error} />}
                    <div className="section">
                      <h4>
                        Segmentation preview{Number.isInteger(segJob.preview_index) ? ` (image ${segJob.preview_index + 1})` : ""}
                      </h4>
                      {lastSegPreviewPayload && Number.isInteger(segJob.preview_index) && (
                        <div className="row row-right">
                          <button
                            className="secondary btn-small"
                            onClick={() =>
                              handleStartSegmentation({
                                ...lastSegPreviewPayload,
                                preview: true,
                                preview_index: (Number(segJob.preview_index) || 0) + 1,
                              })
                            }
                            disabled={["starting", "queued", "running", "canceling"].includes(segJob.status)}
                          >
                            Preview next image
                          </button>
                        </div>
                      )}
                      {(segJob.preview_paths || []).length > 0 ? (
                        <>
                          <div className="viewer-toolbar">
                            <button
                              className="ghost btn-small"
                              onClick={() => setSegPreviewPage((p) => Math.max(0, p - 1))}
                              disabled={segPreviewPage <= 0}
                            >
                              ◀
                            </button>
                            <span className="viewer-counter">
                              {Math.min((segPreviewPage * 2) + 1, segJob.preview_paths.length)}-{Math.min((segPreviewPage * 2) + 2, segJob.preview_paths.length)} / {segJob.preview_paths.length}
                            </span>
                            <button
                              className="ghost btn-small"
                              onClick={() => setSegPreviewPage((p) => {
                                const maxPage = Math.max(0, Math.ceil((segJob.preview_paths.length || 0) / 2) - 1);
                                return Math.min(maxPage, p + 1);
                              })}
                              disabled={((segPreviewPage + 1) * 2) >= segJob.preview_paths.length}
                            >
                              ▶
                            </button>
                          </div>
                          <div className="plot-thumbs plot-thumbs-right">
                            {(segJob.preview_paths || []).slice(segPreviewPage * 2, segPreviewPage * 2 + 2).map((path) => (
                              (() => {
                                const meta = previewMeta(path);
                                return (
                                  <a
                                    key={path}
                                    href={`${API_BASE}/segmentation/file?path=${encodeURIComponent(path)}`}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="thumb-card"
                                  >
                                    <span>
                                      {meta.condition ? `Condition: ${meta.condition}` : ""}
                                      {meta.condition && meta.channel ? " | " : ""}
                                      {meta.channel ? `Channel: ${meta.channel}` : ""}
                                    </span>
                                    <img
                                      src={`${API_BASE}/segmentation/file?path=${encodeURIComponent(path)}&v=${segPreviewNonce}`}
                                      alt={path.split("/").pop()}
                                    />
                                    <span>{path.split("/").pop()}</span>
                                  </a>
                                );
                              })()
                            ))}
                          </div>
                        </>
                      ) : segJob.preview_path ? (
                        <a
                          href={`${API_BASE}/segmentation/file?path=${encodeURIComponent(segJob.preview_path)}`}
                          target="_blank"
                          rel="noreferrer"
                          className="thumb-card viewer-single"
                        >
                          <img
                            src={`${API_BASE}/segmentation/file?path=${encodeURIComponent(segJob.preview_path)}&v=${segPreviewNonce}`}
                            alt={segJob.preview_path.split("/").pop()}
                          />
                          <span>{segJob.preview_path.split("/").pop()}</span>
                        </a>
                      ) : (
                        <p className="hint">No preview image yet.</p>
                      )}
                    </div>
                    <div className="section">
                      <h4>Log</h4>
                      <pre className="seg-log">{segJob.log || "No logs yet."}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="section">
                    <EmptyState
                      title="Segmentation results will appear here"
                      text="Use Preview to inspect a sample image, or Run to process the selected images and follow progress, logs, and generated previews."
                    />
                  </div>
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Gating" ? (
          <>
            <GatingLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onPickDirectory={async () => {
                const res = await pickDirectoryPath();
                return res.path || "";
              }}
              onPreview={handleGatingPreview}
              onApply={handleGatingApply}
              onAxesChanged={() => setGatingStatus({ level: "info", text: "Columns changed. Click Preview gate to draw a new gate for the selected axes." })}
              status={gatingStatus}
              loading={gatingLoading}
              applying={gatingApplying}
              state={gatingState}
              setState={setGatingState}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Gating")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetGatingUi} disabled={gatingLoading || gatingApplying}>
                    Reset
                  </button>
                </div>
                {(gatingLoading || gatingApplying) && (
                  <div className="preview-loading">
                    <div className="spinner" />
                    <div className="hint">{gatingLoading ? "Generating preview..." : "Applying gate..."}</div>
                  </div>
                )}
                {gatingState.figure ? (
                  <>
                    <div className="gate-manual-controls">
                      <div>
                        <h3>Manual gate limits</h3>
                        <p className="hint hint-muted">
                          Optional. Adjust the box directly on the plot, or type exact limits here and apply them.
                        </p>
                      </div>
                      <div className="gate-limit-grid">
                        <label>
                          <span>X min</span>
                          <input className="input" type="number" value={gatingState.x_min} onChange={(e) => setGatingState((prev) => ({ ...prev, x_min: e.target.value }))} />
                        </label>
                        <label>
                          <span>X max</span>
                          <input className="input" type="number" value={gatingState.x_max} onChange={(e) => setGatingState((prev) => ({ ...prev, x_max: e.target.value }))} />
                        </label>
                        <label>
                          <span>Y min</span>
                          <input className="input" type="number" value={gatingState.y_min} onChange={(e) => setGatingState((prev) => ({ ...prev, y_min: e.target.value }))} />
                        </label>
                        <label>
                          <span>Y max</span>
                          <input className="input" type="number" value={gatingState.y_max} onChange={(e) => setGatingState((prev) => ({ ...prev, y_max: e.target.value }))} />
                        </label>
                      </div>
                      <div className="row gate-limit-actions">
                        <button
                          className="secondary"
                          onClick={() => handleGatingPreview()}
                          disabled={gatingLoading || gatingApplying}
                        >
                          Apply limits
                        </button>
                        <button
                          className="ghost"
                          onClick={() => {
                            setGatingState((prev) => ({ ...prev, x_min: "", x_max: "", y_min: "", y_max: "" }));
                            handleGatingPreview({ resetBounds: true });
                          }}
                          disabled={gatingLoading || gatingApplying}
                        >
                          Auto limits
                        </button>
                      </div>
                    </div>
                    <PlotPanel
                      figure={gatingState.figure}
                      onRelayout={handleGatingRelayout}
                      config={{
                        displayModeBar: false,
                        displaylogo: false,
                        responsive: true,
                        scrollZoom: false,
                        edits: { shapePosition: true },
                      }}
                    />
                  </>
                ) : (
                  <EmptyState
                    title="Gate preview will appear here"
                    text="Select one or more datasets, choose the X and Y columns, then run Preview gate to adjust the population box before saving."
                  />
                )}
                {(gatingState.tables || []).length ? (
                  <>
                    {(gatingState.tables || []).map((t) => (
                      <StatsTableView key={`gating-${t.name}`} table={t} onDownload={downloadStatsTableCsv} />
                    ))}
                  </>
                ) : null}
                {(gatingState.files || []).length ? (
                  <div className="section">
                    <h3>Saved files</h3>
                    <pre className="seg-log">{(gatingState.files || []).join("\n")}</pre>
                  </div>
                ) : null}
              </section>
            </main>
          </>
        ) : activeModule === "Tracking" ? (
          <>
            <TrackingLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onPickDirectory={async () => {
                const res = await pickDirectoryPath();
                return res.path || "";
              }}
              onRunAutomatic={handleTrackingRunAutomatic}
              onGoToCorrection={handleTrackingGoToCorrection}
              onOpenCorrection={handleTrackingOpenCorrection}
              onSaveResults={handleTrackingSaveResults}
              onRefreshFrame={handleTrackingRefreshFrame}
              onPrevFrame={() => handleTrackingStepFrame(-1)}
              onNextFrame={() => handleTrackingStepFrame(1)}
              onDeleteTracks={handleTrackingDelete}
              onLinkTracks={handleTrackingLink}
              status={trackingStatus}
              state={trackingState}
              setState={setTrackingState}
              running={trackingRunning}
              loadingFrame={trackingLoadingFrame}
              editing={trackingEditing}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Tracking")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetTrackingUi} disabled={trackingRunning || trackingLoadingFrame || trackingEditing}>
                    Reset
                  </button>
                </div>
                {String(trackingState.workflow_stage || "step1") === "step1" && trackingRunning && (
                  <div className="tracking-run-feedback">
                    <div className="spinner" />
                    <div className="hint hint-muted">
                      Automatic tracking is running. This may take a little while depending on the table size.
                    </div>
                  </div>
                )}
                {(trackingState.preview_image_path || trackingRunning || trackingLoadingFrame || trackingEditing) ? (
                  <div className="section">
                    <h3>Tracking viewer</h3>
                    {String(trackingState.workflow_stage || "step1") === "correction" && (
                      <div className="row" style={{ marginBottom: 8 }}>
                        <button
                          className="ghost"
                          title="Remove the current highlighted selections without changing the tracking table."
                          onClick={() => setTrackingState((prev) => ({ ...prev, selected: [], selected_markers: [] }))}
                          disabled={!(trackingState.selected || []).length}
                        >
                          Clear selection
                        </button>
                        <button className="ghost" title="Restore the table and viewer to the state before the last edit action." onClick={handleTrackingUndo} disabled={!String(trackingState.undo_checkpoint_path || "").trim() || trackingEditing || trackingLoadingFrame || trackingRunning}>
                          Undo
                        </button>
                        <button className="ghost" title="Save the current corrected table to a temporary checkpoint so you can keep working without losing progress." onClick={handleTrackingSaveProgress} disabled={trackingEditing || trackingLoadingFrame || trackingRunning || !String(trackingState.table_path || "").trim()}>
                          Save progress
                        </button>
                        <button className="ghost" title="Link the selected cells into the same track. Across frames, the earliest selected cell becomes the base track." onClick={handleTrackingLink} disabled={(trackingState.selected || []).length < 2}>
                          Link selected
                        </button>
                        <button className="ghost" title="Mark a cell division using exactly 3 selections: the mother cell in the earlier frame and the two daughter cells in the later frame." onClick={handleTrackingDivision} disabled={(trackingState.selected || []).length !== 3}>
                          Cell division
                        </button>
                        <button className="ghost" title="Cut the selected track from that point onward. The chosen cell keeps the old family before that frame, and gets a new number/color from the selected frame to the end." onClick={handleTrackingUnlink} disabled={(trackingState.selected || []).length < 1}>
                          Unlink
                        </button>
                        <button className="ghost" title="Delete the selected track completely from the table and from the rendered tracking view." onClick={handleTrackingDelete} disabled={!(trackingState.selected || []).length}>
                          Delete track
                        </button>
                      </div>
                    )}
                    <div className="viewer-toolbar">
                      <button
                        className="ghost btn-small"
                        title="Show the previous frame in the tracking viewer."
                        onClick={() => handleTrackingStepFrame(-1)}
                        disabled={trackingLoadingFrame || trackingRunning || trackingEditing || Number(trackingState.frame || 0) <= 0}
                      >
                        ◀
                      </button>
                      <span className="viewer-counter">
                        {(Number(trackingState.frame || 0) + 1)} / {(Number(trackingState.max_frame || 0) + 1)}
                      </span>
                      <button
                        className="ghost btn-small"
                        title="Show the next frame in the tracking viewer."
                        onClick={() => handleTrackingStepFrame(1)}
                        disabled={trackingLoadingFrame || trackingRunning || trackingEditing || Number(trackingState.frame || 0) >= Number(trackingState.max_frame || 0)}
                      >
                        ▶
                      </button>
                    </div>
                    {trackingState.preview_image_path ? (
                      <div className="thumb-card viewer-single" style={{ cursor: "crosshair" }}>
                        <div style={{ position: "relative", width: "100%" }}>
                          {(trackingRunning || trackingLoadingFrame || trackingEditing) && (
                            <div className="viewer-overlay">
                              <div className="spinner" />
                              <div className="hint hint-muted">
                                {trackingRunning ? "Running automatic tracking..." : (trackingEditing ? "Applying correction..." : "Updating frame...")}
                              </div>
                            </div>
                          )}
                          <img
                            src={`${API_BASE}/tracking/file?path=${encodeURIComponent(trackingState.preview_image_path)}&v=${trackingState.preview_nonce || 0}`}
                            alt={`tracking-frame-${trackingState.frame || 0}`}
                            onLoad={(e) => {
                              const w = Number(e.currentTarget.naturalWidth || 0);
                              const h = Number(e.currentTarget.naturalHeight || 0);
                              setTrackingState((prev) => ({ ...prev, viewer_w: w, viewer_h: h }));
                            }}
                            onClick={handleTrackingViewerClick}
                          />
                          {(trackingState.selected_markers || [])
                            .filter((m) => Number(m.frame) === Number(trackingState.frame || 0))
                            .map((m, i) => {
                              const w = Number(trackingState.viewer_w || 0);
                              const h = Number(trackingState.viewer_h || 0);
                              if (!w || !h) return null;
                              return (
                                <span
                                  key={`trk-marker-${i}`}
                                  style={{
                                    position: "absolute",
                                    left: `calc(${(Number(m.x) / w) * 100}% - 6px)`,
                                    top: `calc(${(Number(m.y) / h) * 100}% - 6px)`,
                                    width: 12,
                                    height: 12,
                                    borderRadius: "50%",
                                    background: "#C8B6E2",
                                    border: "2px solid #3A6EA5",
                                    pointerEvents: "none",
                                  }}
                                />
                              );
                            })}
                        </div>
                        <span>{trackingState.preview_image_path.split("/").pop()}</span>
                      </div>
                    ) : (
                      <p className="hint hint-muted">
                        Running tracking. The viewer will appear as soon as the first frame is ready.
                        {trackingState.preview_cache_dir ? ` Cache: ${trackingState.preview_cache_dir}` : ""}
                      </p>
                    )}
                    {(trackingState.selected_markers || []).filter((m) => Number(m.frame) === Number(trackingState.frame || 0)).length > 0 && (
                      <div className="hint hint-muted">
                        {(trackingState.selected_markers || [])
                          .filter((m) => Number(m.frame) === Number(trackingState.frame || 0))
                          .map((m, i) => `#${i + 1} x=${Number(m.x).toFixed(1)}, y=${Number(m.y).toFixed(1)}`)
                          .join(" | ")}
                      </div>
                    )}
                  </div>
                ) : (
                  <EmptyState
                    title="Tracking viewer will appear here"
                    text="Run automatic tracking first. Once frames are available, this area becomes the viewer for inspection and manual correction."
                  />
                )}
	                {trackingState.saved_progress_path && (
	                  <p className="hint hint-muted">Saved progress file: {trackingState.saved_progress_path}</p>
	                )}
	                <p className="hint hint-muted">Rows: {trackingState.total_rows || 0} | Tracks: {trackingState.total_tracks || 0} | Frame: {trackingState.frame || 0}/{trackingState.max_frame || 0}</p>
	              </section>
	            </main>
          </>
        ) : activeModule === "Foci Overlay" ? (
          <>
            <FociOverlayLeftPanel
              key={`foci-panel-${fociPanelResetKey}`}
              onPickDirectory={async () => {
                try {
                  const res = await pickDirectoryPath();
                  return res.path || "";
                } catch {
                  return "";
                }
              }}
              onStartFoci={handleStartFoci}
              onStopFoci={handleStopFoci}
              onLoadFociChannels={loadFociChannels}
              fociJob={fociJob}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Foci Overlay")}>
                    Tutorial
                  </button>
                  <button
                    className="ghost btn-small"
                    onClick={handleResetFociUi}
                    disabled={["starting", "queued", "running", "canceling"].includes(fociJob.status || "idle")}
                  >
                    Reset
                  </button>
                </div>
                {fociJob.job_id ? (
                  <div className="section">
                    <h3>Execution progress</h3>
                    <div className="progress-wrap">
                      <div
                        className={`progress-fill ${["starting", "running", "queued", "canceling"].includes(fociJob.status) ? "running" : ""}`}
                        style={{ width: `${Math.max(0, Math.min(100, fociJob.progress || 0))}%` }}
                      />
                    </div>
                    <Status
                      level={fociJob.status === "completed" ? "success" : fociJob.status === "failed" ? "error" : "info"}
                      text={fociJob.message || "Waiting to start."}
                    />
                    {fociJob.error && <Status level="error" text={fociJob.error} />}
                    <div className="section">
                      <h4>Log</h4>
                      <pre className="seg-log">{fociJob.log || "No logs yet."}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="section">
                    <EmptyState
                      title="Foci overlay results will appear here"
                      text="Choose the PKL folder and output options, then run the overlay to monitor progress and review the generated logs."
                    />
                  </div>
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Statistics" ? (
          <>
            <StatsLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onRun={handleStatsRun}
              status={statsStatus}
              loading={statsLoading}
              state={statsState}
              setState={setStatsState}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Statistics")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetStatisticsUi} disabled={statsLoading}>
                    Reset
                  </button>
                </div>
                {statsLoading && (
                  <div className="preview-loading">
                    <div className="spinner" />
                    <div className="hint">Running analysis...</div>
                  </div>
                )}
                {(statsState.tables || []).length ? (
                  <>
                    {(statsState.tables || []).map((t) => (
                      <StatsTableView key={`stats-${t.name}`} table={t} onDownload={downloadStatsTableCsv} />
                    ))}
                    <div className="section">
                      <div className="row row-between">
                        <h3>Log</h3>
                        <div className="row">
                          <button className="ghost btn-small" onClick={copyStatsLogTxt} disabled={!String(statsState.log || "").trim()}>
                            Copy TXT
                          </button>
                          <button className="ghost btn-small" onClick={downloadStatsLogTxt} disabled={!String(statsState.log || "").trim()}>
                            Download TXT
                          </button>
                        </div>
                      </div>
                      <pre className="seg-log">{statsState.log || "No logs yet."}</pre>
                    </div>
                  </>
                ) : (
                  <EmptyState
                    title="Statistics tables will appear here"
                    text="Select the datasets, choose the statistical test, then run the analysis to view result tables and the execution log."
                  />
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Clustering" ? (
          <>
            <ClusteringLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onPreview={handleClusteringPreview}
              onElbow={handleClusteringElbow}
              status={clusteringStatus}
              loading={clusteringLoading}
              elbowLoading={clusteringElbowLoading}
              state={clustering}
              setState={setClustering}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Clustering")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetClusteringUi} disabled={clusteringLoading || clusteringElbowLoading}>
                    Reset
                  </button>
                </div>
                {(clusteringLoading || clusteringElbowLoading) && (
                  <div className="preview-loading">
                    <div className="spinner" />
                    <div className="hint">{clusteringLoading ? "Running embedding..." : "Generating elbow..."}</div>
                  </div>
                )}
                {clustering.figure ? (
                  <PlotPanel figure={clustering.figure} />
                ) : (
                  <EmptyState
                    title="Embedding preview will appear here"
                    text="Load datasets, select numeric features, then run the embedding to inspect clusters or metadata coloring."
                  />
                )}
                {clustering.elbowFigure && (
                  <div className="section">
                    <h3>Elbow Plot</h3>
                    <PlotPanel figure={clustering.elbowFigure} />
                  </div>
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Plot Data" ? (
          <>
            <PlotDataLeftPanel
              onPickCsv={async () => {
                const res = await pickCsvPath();
                return res.path || "";
              }}
              onPreview={handlePlotDataPreview}
              status={plotDataStatus}
              loading={plotDataLoading}
              setStatusExternal={setPlotDataStatusMsg}
              graphState={plotData}
              setGraphState={setPlotData}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Plot Data")}>
                    Tutorial
                  </button>
                  <button className="ghost btn-small" onClick={handleResetPlotDataUi} disabled={plotDataLoading}>
                    Reset
                  </button>
                </div>
                {plotDataLoading && (
                  <div className="preview-loading">
                    <div className="spinner" />
                    <div className="hint">Generating preview...</div>
                  </div>
                )}
                {plotData.figure ? (
                  <PlotPanel figure={plotData.figure} />
                ) : (
                  <EmptyState
                    title="Plot preview will appear here"
                    text="Add at least one CSV dataset, choose the graph options, then click Plot to render an interactive preview."
                  />
                )}
              </section>
            </main>
          </>
        ) : activeModule === "Image Registration" ? (
          <>
            <RegistrationLeftPanel
              key={`reg-panel-${regPanelResetKey}`}
              onPickDirectory={async () => {
                try {
                  const res = await pickDirectoryPath();
                  return res.path || "";
                } catch {
                  return "";
                }
              }}
              onStartRegistration={handleStartRegistration}
              onStopRegistration={handleStopRegistration}
              regJob={regJob}
            />
            <main className="content">
              <section>
                <div className="row row-right">
                  <button className="ghost btn-small" onClick={() => handleOpenTutorial("Image Registration")}>
                    Tutorial
                  </button>
                  <button
                    className="ghost btn-small"
                    onClick={handleResetRegistrationUi}
                    disabled={["starting", "queued", "running", "canceling"].includes(regJob.status || "idle")}
                  >
                    Reset
                  </button>
                </div>
                {regJob.job_id ? (
                  <div className="section">
                    <Status
                      level="warning"
                      text="Registration can be slow and memory-intensive. Keep this window open and avoid running other heavy tasks. If needed, reduce the number of images/channels per run."
                    />
                    <h3>Execution progress</h3>
                    <div className="progress-wrap">
                      <div
                        className={`progress-fill ${["starting", "running", "queued", "canceling"].includes(regJob.status) ? "running" : ""}`}
                        style={{ width: `${Math.max(0, Math.min(100, regJob.progress || 0))}%` }}
                      />
                    </div>
                    <Status
                      level={regJob.status === "completed" ? "success" : regJob.status === "failed" ? "error" : "info"}
                      text={regJob.message || "Waiting to start."}
                    />
                    {(regJob.total || 0) > 0 && (
                      <div className="hint">{regJob.done || 0} / {regJob.total || 0} conditions</div>
                    )}
                    {regJob.error && <Status level="error" text={regJob.error} />}
                    <div className="section">
                      <h4>Log</h4>
                      <pre className="seg-log">{regJob.log || "No logs yet."}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="section">
                    <EmptyState
                      title="Registration progress will appear here"
                      text="Load image folders and run registration to monitor progress, status messages, and the execution log."
                    />
                  </div>
                )}
              </section>
            </main>
          </>
        ) : (
          <>
        <Card as="aside" className="panel nma-panel seg-panel" variant="panel">
          <div className="seg-header">
            <h3>NMA Settings</h3>
            <p className="hint">Add at least one control only if you want to create new settings. If loading existing settings, this is not required.</p>
          </div>
          <div className="row row-right">
            <Button className="ghost btn-small bulk-expander-button" onClick={() => setAllCollapsed(true)}>
              <span>Collapse all</span>
            </Button>
            <Button className="ghost btn-small bulk-expander-button" onClick={() => setAllCollapsed(false)}>
              <span>Expand all</span>
            </Button>
          </div>

          {rows.map((row, idx) => (
            <Card className="dataset" variant="dataset" key={row.id}>
              <div className="row dataset-header-row">
                <DatasetCollapseButton collapsed={!!collapsedById[row.id]} onClick={() => toggleDatasetCollapse(row.id)} label={row.name || `Dataset ${idx + 1}`} />
                <div className="dataset-title">
                  {row.name?.trim() || `Dataset ${idx + 1}`}{row.is_control ? " (Control)" : ""}
                </div>
                <DatasetBadge>#{idx + 1}</DatasetBadge>
              </div>
              {!collapsedById[row.id] && (
                <>
                  <div className="row">
                    <div style={{ flex: 1 }}>
                      <FieldTitle title="Dataset name" tip="Friendly name used to identify this dataset throughout the NMA workflow." className="field-head" />
                      <input
                        className="input"
                        placeholder="Name"
                        value={row.name}
                        onChange={(e) => updateRow(idx, { name: e.target.value })}
                      />
                    </div>
                    <label className="checkbox">
                      <input
                        type="checkbox"
                        checked={row.is_control}
                        onChange={(e) => updateRow(idx, { is_control: e.target.checked })}
                      />
                      Control
                    </label>
                  </div>
                  <div className="row path-row">
                    <div style={{ flex: 1 }}>
                      <FieldTitle title="CSV path" tip="Results table used as input for this NMA dataset." className="field-head" />
                      <input
                        className="input"
                        placeholder="/path/Results.csv"
                        value={row.path}
                        onChange={(e) => updateRow(idx, { path: e.target.value })}
                      />
                    </div>
                    <Button
                      className="secondary"
                      title="Choose a CSV file for this NMA dataset."
                      onClick={async () => {
                        setStatus("Opening file picker...");
                        setStatusLevel("info");
                        try {
                          const res = await pickCsvPath();
                          updateRow(idx, { path: res.path || "" });
                          setStatus("Path selected.");
                          setStatusLevel("success");
                        } catch (err) {
                          setStatus(errorMessageFromException(err, "Could not open the CSV picker. Check that the backend is running, then choose the file again."));
                          setStatusLevel("error");
                        }
                      }}
                    >
                      <BrowseLabel>Browse CSV</BrowseLabel>
                    </Button>
                  </div>
                  <div className="row">
                    <div style={{ flex: 1 }}>
                      <FieldTitle title="Area column" tip="Column used as the Area axis/input for NMA calculations. If both nuclear and cytoplasm area columns exist, choose one explicitly." className="field-head" />
                      <select
                        className="input"
                        value={row.area_col}
                        onChange={(e) => updateRow(idx, { area_col: e.target.value })}
                      >
                        {(row.columns || []).length > 0 && <option value="">Select area column...</option>}
                        {(row.columns || ["Area"]).map((c) => (
                          <option key={`area-${idx}-${c}`} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                    <div style={{ flex: 1 }}>
                      <FieldTitle title="NII column" tip="Column used as the NII axis/input for NMA calculations. If both nuclear and cytoplasm NII columns exist, choose one explicitly." className="field-head" />
                      <select
                        className="input"
                        value={row.nii_col}
                        onChange={(e) => updateRow(idx, { nii_col: e.target.value })}
                      >
                        {(row.columns || []).length > 0 && <option value="">Select NII column...</option>}
                        {(row.columns || ["NII"]).map((c) => (
                          <option key={`nii-${idx}-${c}`} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="row row-right">
                    <Button
                      className="ghost"
                      title="Read the CSV header and populate the Area/NII selectors for this dataset."
                      onClick={async () => {
                        setStatus("Loading columns...");
                        setStatusLevel("info");
                        try {
                          const res = await callApi("/nma/datasets/columns", { path: row.path });
                          const cols = res.columns || [];
                          const areaGuess = pickNmaMeasureColumn(cols, "Area", row.area_col, res.area_columns || []);
                          const niiGuess = pickNmaMeasureColumn(cols, "NII", row.nii_col, res.nii_columns || []);
                          updateRow(idx, {
                            columns: cols,
                            area_columns: res.area_columns || [],
                            nii_columns: res.nii_columns || [],
                            area_col: areaGuess,
                            nii_col: niiGuess,
                          });
                          if (!areaGuess || !niiGuess) {
                            setStatus("Columns loaded. Choose Area and NII explicitly for this dataset.");
                            setStatusLevel("warning");
                          } else {
                            setStatus("Columns loaded.");
                            setStatusLevel("success");
                          }
                        } catch (err) {
                          setStatus(errorMessageFromException(err, "Columns could not be loaded from this CSV. Check that the file exists, is not empty, and has readable column headers."));
                          setStatusLevel("error");
                        }
                      }}
                      disabled={!row.path.trim()}
                    >
                      Load columns
                    </Button>
                    {rows.length > 1 && (
                      <Button className="ghost" onClick={() => {
                        if (confirmRemoveFilled(row, `Dataset ${idx + 1}`)) removeRow(idx);
                      }}>Remove</Button>
                    )}
                  </div>
                </>
              )}
            </Card>
          ))}

          <Button className="secondary add-dataset-button" onClick={addRow}>Add dataset</Button>

          {showPlotConfig && (
          <div className={`section nma-plot-config ${highlightPlotConfig ? "nma-plot-config-highlight" : ""}`}>
              <>
                <div className="row row-between">
                  <h4 style={{ margin: 0 }}>NMA analysis</h4>
                  <Button className="ghost btn-small" onClick={() => setShowPlotConfig(false)}>
                    Back to NMA settings
                  </Button>
                </div>
                <p className="hint">Choose how you want to plot NMA (dot plot or heatmap).</p>
                <div className="row">
                  <label
                    className="radio"
                  >
                    <input
                      type="radio"
                      name="plot-kind"
                      checked={plotConfig.kind === "dot"}
                      onChange={() => setPlotConfig((prev) => ({ ...prev, kind: "dot" }))}
                    />
                    Dot plot
                    <Tip text="Dot plot: each nucleus is displayed as an individual point." />
                  </label>
                  <label
                    className="radio"
                  >
                    <input
                      type="radio"
                      name="plot-kind"
                      checked={plotConfig.kind === "heatmap"}
                      onChange={() => setPlotConfig((prev) => ({ ...prev, kind: "heatmap" }))}
                    />
                    Heatmap
                    <Tip text="Heatmap: show density patterns, useful for larger datasets." />
                  </label>
                </div>
                {plotConfig.kind === "dot" ? (
                  <>
                    <div className="hint">
                      Dot plot options <Tip text="These selectors use columns detected from your loaded dataset tables." />
                    </div>
                    <FieldTitle title="Color by (column1)" tip="Choose which dataset column controls marker color." className="field-head" />
                    <div className="row">
                      <select
                        className="input"
                        value={plotConfig.dot.column1}
                        onChange={(e) => updateDotConfig({ column1: e.target.value })}
                        disabled={allDetectedColumns.length === 0}
                      >
                        <option value="">
                          {allDetectedColumns.length ? "Color by (column1)" : "Load columns first"}
                        </option>
                        {allDetectedColumns.map((c) => (
                          <option key={`dot-c1-${c}`} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                    <FieldTitle title="Size by (column2)" tip="Choose which dataset column controls marker size." className="field-head" />
                    <div className="row">
                      <select
                        className="input"
                        value={plotConfig.dot.column2}
                        onChange={(e) => updateDotConfig({ column2: e.target.value })}
                        disabled={allDetectedColumns.length === 0}
                      >
                        <option value="">
                          {allDetectedColumns.length ? "Size by (column2)" : "Load columns first"}
                        </option>
                        {allDetectedColumns.map((c) => (
                          <option key={`dot-c2-${c}`} value={c}>{c}</option>
                        ))}
                      </select>
                    </div>
                    <div className="row">
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Hue minimum" tip="Optional lower bound for the color scale. Leave empty for automatic scaling." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          placeholder="Hue min (optional)"
                          value={plotConfig.dot.hue_min}
                          onChange={(e) => updateDotConfig({ hue_min: e.target.value })}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Hue maximum" tip="Optional upper bound for the color scale. Leave empty for automatic scaling." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          placeholder="Hue max (optional)"
                          value={plotConfig.dot.hue_max}
                          onChange={(e) => updateDotConfig({ hue_max: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="row">
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Size minimum" tip="Optional lower bound for marker size scaling." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          placeholder="Size min (optional)"
                          value={plotConfig.dot.size_min}
                          onChange={(e) => updateDotConfig({ size_min: e.target.value })}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Size maximum" tip="Optional upper bound for marker size scaling." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          placeholder="Size max (optional)"
                          value={plotConfig.dot.size_max}
                          onChange={(e) => updateDotConfig({ size_max: e.target.value })}
                        />
                      </div>
                    </div>
                    <div className="row">
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Sample size" tip="Optional limit on how many nuclei are sampled into the dot plot." className="field-head" />
                        <input
                          className="input"
                          type="number"
                          min="1"
                          placeholder="Sample size (optional)"
                          value={plotConfig.dot.sample_size}
                          onChange={(e) => updateDotConfig({ sample_size: e.target.value })}
                        />
                      </div>
                      <div style={{ flex: 1 }}>
                        <FieldTitle title="Palette" tip="Optional color palette used for the dot plot." className="field-head" />
                        <select
                          className="input"
                          value={plotConfig.dot.palette}
                          onChange={(e) => updateDotConfig({ palette: e.target.value })}
                        >
                          <option value="">Palette (optional)</option>
                          {PALETTE_OPTIONS.map((p) => (
                            <option key={`pal-${p}`} value={p}>{p}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                    <div className="check-grid">
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.dot.single}
                          onChange={(e) => updateDotConfig({ single: e.target.checked })}
                        />
                        Single plot
                        <Tip text="Combine all datasets in one view." />
                      </label>
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.dot.overtime}
                          onChange={(e) => updateDotConfig({ overtime: e.target.checked })}
                        />
                        Overtime
                        <Tip text="Use time-sequence style when temporal data is available." />
                      </label>
                    </div>
                  </>
                ) : (
                  <>
                    <FieldTitle title="Heatmap palette" tip="Color palette used for heatmap rendering." className="field-head" />
                    <div className="row">
                      <select
                        className="input"
                        value={plotConfig.heatmap.palette}
                        onChange={(e) => updateHeatmapConfig({ palette: e.target.value })}
                      >
                        <option value="">Palette (optional)</option>
                        {PALETTE_OPTIONS.map((p) => (
                          <option key={`heat-pal-${p}`} value={p}>{p}</option>
                        ))}
                      </select>
                    </div>
                    <div className="check-grid">
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.heatmap.single}
                          onChange={(e) => updateHeatmapConfig({ single: e.target.checked })}
                        />
                        Single plot
                        <Tip text="Combine all datasets in one heatmap view." />
                      </label>
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.heatmap.overtime}
                          onChange={(e) => updateHeatmapConfig({ overtime: e.target.checked })}
                        />
                        Overtime
                        <Tip text="Use time-sequence heatmap when temporal data is available." />
                      </label>
                      <label className="checkbox">
                        <input
                          type="checkbox"
                          checked={plotConfig.heatmap.jointplot}
                          onChange={(e) => updateHeatmapConfig({ jointplot: e.target.checked })}
                        />
                        Jointplot
                        <Tip text="Include marginal histograms alongside the heatmap." />
                      </label>
                    </div>
                  </>
                )}
                <FieldTitle title="Saving path" tip="Directory where NMA plots and outputs will be saved." className="field-head" />
                <div className="row path-row">
                  <input
                    className="input"
                    placeholder="Folder to save NMA results"
                    value={plotSavePath}
                    onChange={(e) => setPlotSavePath(e.target.value)}
                  />
                  <Button
                    className="secondary"
                    title="Choose where the generated NMA plots should be saved."
                    onClick={async () => {
                      try {
                        const res = await pickDirectoryPath();
                        setPlotSavePath(res.path || "");
                      } catch (err) {
                        setStatus(errorMessageFromException(err, "Could not open the folder picker. Check that the backend is running, then choose the output folder again."));
                        setStatusLevel("error");
                      }
                    }}
                  >
                    <BrowseLabel>Browse</BrowseLabel>
                  </Button>
                </div>
                <Button
                  className="primary"
                  title="Generate all NMA plots with the current plotting settings and save them to the selected folder."
                  onClick={handlePlotAll}
                  disabled={!plotSavePath.trim() || datasets.length === 0 || (plotJob.status === "running" || plotJob.status === "queued")}
                >
                  Plot all
                </Button>
                <div className="hint">
                  Generate plots with current settings and save them to the chosen folder.
                </div>
              </>
          </div>
          )}

          {!showPlotConfig && step === 2 && (
            <div className="section">
              <h4>Thresholds</h4>
              {Object.keys(thresholds).map((k) => (
                <div className="row" key={k}>
                  <label className="label">{k}</label>
                  <div className="readonly">{Number(thresholds[k]).toFixed(3)}</div>
                </div>
              ))}
            </div>
          )}

          {!showPlotConfig && (
            <div className="section">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pkl,.pickle"
                style={{ display: "none" }}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleLoadSettings(f);
                }}
              />
              <Button
                className="secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={step1Ready}
              >
                Load settings
              </Button>
              {!controlGateReady && !step1Ready && (
                <Button className="primary" onClick={handleControlGate} disabled={!hasControl}>Create Settings</Button>
              )}
            </div>
          )}
          <Status level={statusLevel} text={status} />
        </Card>

        <main className="content">
          {!step1Ready ? (
            <section>
              {renderNmaStepControls()}
              <h2>Step 1 · Control gate</h2>
              <p className="hint">
                Use the box to remove control cells that look like outliers. Cells with unusually high or low Area or NII can distort the NMA settings, so keep the clean central control population for the ellipse in the next step.
              </p>
              {controlGateFigure ? (
                <>
                  <PlotPanel
                    figure={controlGateFigure}
                    onRelayout={handleNmaGateRelayout}
                    config={{
                      displayModeBar: false,
                      displaylogo: false,
                      responsive: true,
                      scrollZoom: false,
                      editable: true,
                      edits: {
                        shapePosition: true,
                        annotationPosition: false,
                        annotationText: false,
                        titleText: false,
                        axisTitleText: false,
                      },
                    }}
                  />
                  {controlGateMeta && (
                    <p className="hint">
                      Kept {controlGateMeta.kept}/{controlGateMeta.total} control cells ({Number(controlGateMeta.kept_percent || 0).toFixed(1)}%).
                    </p>
                  )}
                </>
              ) : (
                <EmptyState
                  title="Control gate will appear here"
                  text="Mark at least one dataset as control, choose the Area and NII columns, then click Create Settings to draw the initial normal-population gate."
                />
              )}
            </section>
          ) : (
            <>
          {step === 0 && (
            <section>
              {renderNmaStepControls()}
              <h2>Step 1 · Control gate</h2>
              <p className="hint">
                Use the box to remove control cells that look like outliers. Cells with unusually high or low Area or NII can distort the NMA settings, so keep the clean central control population for the ellipse in Step 2.
              </p>
              {controlGateFigure && (
                <>
                  <PlotPanel
                    figure={controlGateFigure}
                    onRelayout={handleNmaGateRelayout}
                    config={{
                      displayModeBar: false,
                      displaylogo: false,
                      responsive: true,
                      scrollZoom: false,
                      editable: true,
                      edits: {
                        shapePosition: true,
                        annotationPosition: false,
                        annotationText: false,
                        titleText: false,
                        axisTitleText: false,
                      },
                    }}
                  />
                  {controlGateMeta && (
                    <p className="hint">
                      Kept {controlGateMeta.kept}/{controlGateMeta.total} control cells ({Number(controlGateMeta.kept_percent || 0).toFixed(1)}%).
                    </p>
                  )}
                </>
              )}
            </section>
          )}
          {step === 1 && (
            <section>
              {renderNmaStepControls()}
              <h2>Step 2 · Control ellipse</h2>
              <p className="hint">
                The ellipse defines the Normal subpopulation used in the nuclear morphometry analysis. It is based on the gated control cells from Step 1 and represents nuclei expected to be healthy; adjust the Area and NII SDs manually or use auto-DBSCAN.
              </p>
              <div className="row row-right" style={{ marginBottom: 8 }}>
                <Button className="secondary" onClick={handleAutoDbscan}>Auto (DBSCAN)</Button>
              </div>
              <div className="plot-shell">
                <div className="slider-vertical">
                  <label>Area SD <Tip text="Adjust Area standard deviation for threshold and ellipse height." /></label>
                  <input
                    className="sd-number-input"
                    type="number"
                    min="0"
                    max="5"
                    step="0.1"
                    value={Number.isFinite(sdArea) ? sdArea.toFixed(2) : ""}
                    onChange={(e) => updateNmaAreaSd(parseFloat(e.target.value || "0"))}
                  />
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="0.1"
                    value={5 - sdArea}
                  onChange={(e) => {
                      updateNmaAreaSd(5 - parseFloat(e.target.value || "0"));
                    }}
                  />
                  <span className="slider-value">{sdArea.toFixed(2)}</span>
                </div>
                <PlotPanel figure={step1Figure} />
              </div>
              <div className="slider-horizontal">
                <label>NII SD <Tip text="Adjust NII standard deviation for threshold and ellipse width." /></label>
                <div className="sd-range-row">
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="0.1"
                    value={sdNii}
                    onChange={(e) => {
                      updateNmaNiiSd(parseFloat(e.target.value || "0"));
                    }}
                  />
                  <input
                    className="sd-number-input"
                    type="number"
                    min="0"
                    max="5"
                    step="0.1"
                    value={Number.isFinite(sdNii) ? sdNii.toFixed(2) : ""}
                    onChange={(e) => updateNmaNiiSd(parseFloat(e.target.value || "0"))}
                  />
                </div>
                <span className="slider-value">{sdNii.toFixed(2)}</span>
              </div>
            </section>
          )}

          {step === 2 && (
            <section>
              {renderNmaStepControls()}
              <h2>Step 3 · Threshold lines</h2>
              {!showPlotConfig && (
                <p className="hint">
                  Drag and drop the purple vertical lines to set the NMA population thresholds. The horizontal lines are fixed, and the percentage boxes update automatically from the line positions.
                </p>
              )}
              {(showPlotConfig && showPlotProgress && !showNmaPreviewWhilePlotting) ? (
                <div className="hint">
                  NMA preview and quadrant table are minimized while plotting.
                  <Button
                    className="ghost btn-small"
                    style={{ marginLeft: 8 }}
                    onClick={() => setShowNmaPreviewWhilePlotting(true)}
                  >
                    Show preview
                  </Button>
                </div>
              ) : (
                <>
                  {showPlotConfig && showPlotProgress && (
                    <div className="row row-right" style={{ marginBottom: 8 }}>
                      <Button
                        className="ghost btn-small"
                        onClick={() => setShowNmaPreviewWhilePlotting(false)}
                      >
                        Minimize preview
                      </Button>
                    </div>
                  )}
                  {step2Figure ? (
                    <PlotPanel
                      figure={step2Figure}
                      config={{
                        displayModeBar: false,
                        displaylogo: false,
                        editable: !finalMode,
                        edits: {
                          shapePosition: !finalMode,
                          annotationPosition: false,
                          annotationText: false,
                          titleText: false,
                          axisTitleText: false,
                          legendPosition: false,
                          colorbarPosition: false,
                        },
                      }}
                      onRelayout={(ev) => {
                        if (finalMode) return;
                        if (!step2GraphLimits || !step2Stats || !step2Traces) return;
                        const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
                        const toFinite = (value) => {
                          const n = Number(value);
                          return Number.isFinite(n) ? n : null;
                        };
                        const getShape = (idx) => {
                          const x0 = ev[`shapes[${idx}].x0`];
                          const x1 = ev[`shapes[${idx}].x1`];
                          const n0 = toFinite(x0);
                          const n1 = toFinite(x1);
                          if (n0 != null && n1 != null) return (n0 + n1) / 2;
                          return n0 ?? n1;
                        };
                        const shapeChanged = (idx) =>
                          Object.keys(ev || {}).some((key) => key.startsWith(`shapes[${idx}]`));
                        const horizontalChanged = shapeChanged(0) || shapeChanged(1);
                        const verticalChanged = [2, 3, 4, 5].some(shapeChanged);
                        const v_down = getShape(2);
                        const v_down2 = getShape(3);
                        const v_mid = getShape(4);
                        const v_up = getShape(5);
                        if (!horizontalChanged && !verticalChanged) return;
                        const xMin = step2GraphLimits[2];
                        const xMax = step2GraphLimits[3];
                        const next = {
                          ...thresholds,
                          v_down: v_down == null ? thresholds.v_down : clamp(v_down, xMin, xMax),
                          v_down2: v_down2 == null ? thresholds.v_down2 : clamp(v_down2, xMin, xMax),
                          v_mid: v_mid == null ? thresholds.v_mid : clamp(v_mid, xMin, xMax),
                          v_up: v_up == null ? thresholds.v_up : clamp(v_up, xMin, xMax),
                        };
                        setThresholds(next);
                        setStep2Figure(buildStep2Figure(step2Traces, step2Stats, step2GraphLimits, next, sdNii, sdArea, true));
                        setStep2Percentages(computeQuadrantPercentages(step2Traces, next, step2Stats, sdArea));
                        setFinalMode(false);
                      }}
                    />
                  ) : (
                    <div className="hint">Click Next to generate the Step 3 figure.</div>
                  )}
                  {step2Percentages && (
                    (() => {
                      const datasetNames = Array.from(
                        new Set(
                          Object.values(step2Percentages).flatMap((v) => Object.keys(v)).concat(
                            (step2Traces || []).map((t) => t.name).filter(Boolean)
                          )
                        )
                      );
                      return (
                        <div className="percentages">
                          <h3>Quadrant distribution (%)</h3>
                          <div className="percent-table">
                            <div className="percent-row header">
                              <div className="cell">Quadrant</div>
                              {datasetNames.map((name) => (
                                <div className="cell" key={`h-${name}`}>{name}</div>
                              ))}
                            </div>
                            {["LR", "LI", "N", "I", "SR", "S", "SI"].map((q) => (
                              <div className="percent-row" key={`q-${q}`}>
                                <div className="cell">{q}</div>
                                {datasetNames.map((name) => (
                                  <div className="cell" key={`${q}-${name}`}>
                                    {step2Percentages[q]?.[name] != null ? step2Percentages[q][name].toFixed(1) : "-"}
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })()
                  )}
                </>
              )}
              {(!showPlotConfig || !showPlotProgress || !hasPlotRun || showNmaPreviewWhilePlotting) && finalMode && downloadReady && (
                <div className="section">
                  <Button
                    className="secondary"
                    onClick={handleDownloadTable}
                    disabled={!step2Percentages}
                  >
                    Download table
                  </Button>
                </div>
              )}
              {showPlotConfig && showPlotProgress && (
                <div className="section">
                  <h3>Plot progress</h3>
                  <div className="progress-wrap">
                    <div
                      className={`progress-fill ${plotJob.status === "running" || plotJob.status === "queued" ? "running" : ""}`}
                      style={{ width: `${Math.max(0, Math.min(100, plotJob.progress || 0))}%` }}
                    />
                  </div>
                  <div className="hint">{plotJob.message || "Waiting to start."}</div>
                  {plotJob.files?.length > 0 && (
                    <div className="plot-viewer">
                      <div className="viewer-toolbar">
                        <Button
                          className="ghost btn-small"
                          onClick={() => setCurrentPlotIndex((i) => Math.max(0, i - 1))}
                          disabled={currentPlotIndex <= 0}
                        >
                          ◀
                        </Button>
                        <span className="viewer-counter">
                          {currentPlotIndex + 1} / {plotJob.files.length}
                        </span>
                        <Button
                          className="ghost btn-small"
                          onClick={() => setCurrentPlotIndex((i) => Math.min(plotJob.files.length - 1, i + 1))}
                          disabled={currentPlotIndex >= plotJob.files.length - 1}
                        >
                          ▶
                        </Button>
                      </div>
                      <a
                        href={`${API_BASE}/nma/plots/file?path=${encodeURIComponent(plotJob.files[currentPlotIndex])}`}
                        target="_blank"
                        rel="noreferrer"
                        className="thumb-card viewer-single"
                      >
                        <img
                          src={`${API_BASE}/nma/plots/file?path=${encodeURIComponent(plotJob.files[currentPlotIndex])}`}
                          alt={plotJob.files[currentPlotIndex].split("/").pop()}
                        />
                        <span>{plotJob.files[currentPlotIndex].split("/").pop()}</span>
                      </a>
                    </div>
                  )}
                </div>
              )}
            </section>
          )}
            </>
          )}
        </main>
          </>
        )}
      </div>
    </div>
  );
}
