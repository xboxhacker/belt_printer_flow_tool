## Belt Printer Flow Cylinder Generator

# Description
This utility extends 3D belt printer G-code files by adding a cylindrical spiral vase continuation at the end of your print. The script automatically positions a cylinder at the center of your print's X/Y coordinates and starts it at the second-to-last layer height for optimal adhesion.

3 Features
-Automatic Print Analysis: Scans your base G-code to find the optimal starting position and height
-Precise Centering: Calculates the true center of your print for perfect cylinder placement
-Flow Rate Control: Uses M221 commands to adjust extrusion flow rates as the cylinder grows
-Sectioned Printing: Divides the cylinder into sections with progressive flow rate increases
-Visual Interface: Simple GUI for adjusting all parameters without editing G-code manually

# How It Works
-Load a completed belt printer G-code file (must be in the same directory as "base.gcode")
-The script analyzes the file to find the second-to-last layer height and the overall center
-It then generates a precisely positioned cylindrical continuation using spiral vase mode
-Flow rate is automatically adjusted for each section to compensate for belt movement

# Parameters
-Layer Height: Height of each printed layer in the cylinder (it will try and get the height from the base.gcode file)
-Section Height: Height of each flow adjustment section in mm
-Initial Flow Rate: Starting flow percentage (it will try and get the stating flow from the base.gcode file)
-Flow Increase per Section: Percentage to increase flow with each new section
-Number of Sections: Total sections to print
-Cylinder Diameter: Diameter of the printed cylinder

# Usage
Place your belt printer G-code file in the same directory as the script, named "base.gcode"
Run the script and adjust parameters as needed
Click "Generate G-code" to create a new file named "output.gcode"
The output file contains your original print plus the cylinder continuation

# Requirements
Python 3.x with Tkinter
A base G-code file from a belt printer
The base G-code must contain at least two layers
This tool is especially useful for continuous printing applications where a cylindrical extension with adjustable flow rates is needed at precise coordinates.
