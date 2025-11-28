# 6-6 Stewart Platform Inverse Kinematics Calculator and Workspace Analyzer

Original author:       Joe Brown (CSU Sacramento) – August 4, 2006 - https://github.com/jotux/Steward-Platform-Forward-Kinematics-Solver

Modified by:     Adam B. Johnson (University of Victoria) – August 2022 to April 2025

==========================

A MATLAB-based GUI tool for designing, analyzing, and visualizing hexapod (6-6 Stewart Platform) inverse kinematics, including reachable and orientation workspace plotting, and configuration file management.

Key Features:
-------------
- Interactive GUI for configuring base and platform geometry
- Save configuration and hexapod state to .txt format
- Inverse kinematics solver (pose → leg lengths)
- Reachable and orientation workspace visualizations
- Resolution control for workspace simulation accuracy vs speed
- Console-style feedback window for tracking simulation progress
- Export of workspace results to .mat and .png formats


How to Run:
-----------
1. Open MATLAB.
2. Set the working directory to this folder and all subfolders.
3. Run:
       >> RUN_HEXAPOD_CALCULATOR

Usage Tips:
-----------
- Use 'Save Everything' to export/save the window configuration (formdata.txt).
- Use the UI buttons to perform inverse kinematics or workspace plots given an input focus pose.
- Home or Zero the input focus values for quick trials of different positions.
- Apply and track a constant ± offset to base or platform joint X and/or Y positions.
- Select workspace analysis resolution before running simulations for performance control.
- Data exports (.mat) are automatic after drawing figures.
- Use NEW or RECALLed workspace data (.mat) to export PNG files.
- Export a series of PNG images at evenly spaced angles around the workspace plots to generate videos or GIFs offline.

Dependencies:
-------------
- MATLAB (R2020b or later recommended) with GUI support enabled
- 64-bit Windows operating system (tested on Windows 11)
- Precompiled 64-bit MEX files (included)

File Overview:
--------------
- RUN_HEXAPOD_CALCULATOR.m    : Main entry point
- MAIN_GUI.m                  : GUI layout and logic
- *various_functions*.m       : Solvers, button handlers, savers, and visualization functions
- formdata.txt                : Platform and system configuration save file
- *.mat / *.png               : Generated workspace outputs
