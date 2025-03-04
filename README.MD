# Belt Printer Flow Cylinder Generator

## Description
This utility extends 3D belt printer G-code files by adding a cylindrical spiral vase continuation at the end of a predefined 45-degree base. This is called the `base.gcode` file. The script automatically positions a cylinder at the center of your print's X/Y coordinates and starts it in the last layer of the `base.gcode` file.

The `base.gcode` is a basic gcode output file from IdeaMaker Slicer for a belt printer. I have attached the STL to this repo. You can make your own `base.gcode` file to match your printed setup. This tool will *ONLY* work with IdeaMaker gcode and *ONLY* with the `base.STL` sliced file, saved as `base.gcode`.

(https://github.com/xboxhacker/belt_printer_flow_tool/blob/main/preview.png)


## Features
- Automatic Print Analysis: Scans your the base G-code to find the optimal starting position and height (if you have made your own)
- Precise Centering: Calculates the true center of your print for perfect cylinder placement
- Flow Rate Control: Uses M221 commands to adjust extrusion flow rates as the cylinder grows
- Sectioned Printing: Divides the cylinder into sections with progressive flow rate increases
- Visual Interface: Simple GUI for adjusting all parameters without editing G-code manually

## How It Works
- Load the completed belt printer G-code file, `base.gcode`, in the same directory as the script.
- The script analyzes the file to find the last layer height and the overall center
- It then generates a precisely positioned cylindrical continuation using spiral vase mode
- Flow rate is automatically adjusted for each section to compensate for belt movement

## Parameters
- Layer Height: Height of each printed layer in the cylinder (it will try and get the height from the `base.gcode` file)
- Section Height: Height of each flow adjustment section in mm
- Initial Flow Rate: Starting flow percentage (it will try and get the stating flow from the `base.gcode` file)
- Flow Increase per Section: Percentage to increase flow with each new section
- Number of Sections: Total sections to print
- Cylinder Diameter: Diameter of the printed cylinder

## Usage
- Place the `base.gcode` sliced file in the same directory as the `belt_printer_flow_tool.py`
- Run the script and adjust parameters as needed
- Click "Generate G-code" to create a new file named "output.gcode"
- The output file contains the original `base.gcode` print plus the cylinder continuation with flow adjustments

## Requirements
- Python 3.x with Tkinter
- A base G-code file from a belt printer (example in this repo)
- The base G-code must contain at least two layers
