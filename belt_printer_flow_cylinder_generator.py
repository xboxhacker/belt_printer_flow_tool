import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import os
import re
import math
import datetime

class GCodeGenerator:
    def __init__(self, base_gcode, layer_height, section_height, initial_flow_rate, bed_temp, nozzle_temp, 
                 flow_increase, num_sections, nozzle_diameter, cylinder_diameter):
        self.base_gcode = base_gcode
        self.layer_height = layer_height
        self.section_height = section_height
        self.initial_flow_rate = initial_flow_rate  # Now in percentage
        self.bed_temp = bed_temp
        self.nozzle_temp = nozzle_temp
        self.flow_increase = flow_increase  # Now in percentage
        self.num_sections = num_sections
        self.nozzle_diameter = nozzle_diameter
        self.cylinder_diameter = cylinder_diameter
        self.cylinder_radius = cylinder_diameter / 2
        
        # Find all layer heights
        self.layer_heights = self.find_layer_heights()
        
        # Get last and second-to-last layer heights
        if len(self.layer_heights) >= 2:
            self.last_z = self.layer_heights[-1]
            self.second_last_z = self.layer_heights[-2]
            print(f"Last layer Z height: {self.last_z:.3f} mm")
            print(f"Second-to-last layer Z height: {self.second_last_z:.3f} mm")
        else:
            self.last_z = self.layer_heights[-1] if self.layer_heights else 0
            self.second_last_z = 0
            print(f"Last layer Z height: {self.last_z:.3f} mm")
            print(f"WARNING: Could not find second-to-last layer, defaulting to 0")
        
        # Find the true center of the entire print
        self.min_x, self.max_x, self.min_y, self.max_y = self.find_overall_bounding_box()
        self.center_x = (self.min_x + self.max_x) / 2
        self.center_y = (self.min_y + self.max_y) / 2
        
        print(f"Using overall center of print: X={self.center_x:.2f}, Y={self.center_y:.2f}")
        
        # Set starting Z to the second-to-last layer
        self.start_z = self.second_last_z
        
        # Extract PRINT_END sequence if it exists
        self.print_end_sequence = self.extract_print_end_sequence()

    def find_layer_heights(self):
        """Find all unique layer heights in the gcode file"""
        z_heights = set()
        
        for line in self.base_gcode.splitlines():
            if line.startswith("G0 ") or line.startswith("G1 "):
                z_match = re.search(r'Z([0-9]+\.?[0-9]*)', line)
                if z_match:
                    z = float(z_match.group(1))
                    z_heights.add(z)
        
        # Sort the heights from lowest to highest
        z_heights = sorted(list(z_heights))
        print(f"Found {len(z_heights)} unique layer heights in base file")
        
        return z_heights

    def extract_print_end_sequence(self):
        """Extract PRINT_END sequence from the base gcode file"""
        print_end_sequence = ""
        print_end_found = False
        print_end_lines = []
        
        # Look for PRINT_END macro or section
        for line in self.base_gcode.splitlines():
            if "PRINT_END" in line or (print_end_found and not line.strip()):
                print_end_found = True
                print_end_lines.append(line)
                
        if print_end_lines:
            print_end_sequence = "\n".join(print_end_lines)
            print("Found PRINT_END sequence in base file")
        
        return print_end_sequence
    
    def remove_print_end_sequence(self):
        """Remove PRINT_END sequence from base gcode"""
        if not self.print_end_sequence:
            return self.base_gcode
            
        # Remove the PRINT_END sequence from base gcode
        base_without_end = self.base_gcode
        if self.print_end_sequence in base_without_end:
            base_without_end = base_without_end.replace(self.print_end_sequence, "")
            print("Removed PRINT_END sequence from base file")
        
        return base_without_end

    def find_overall_bounding_box(self):
        """Find the X/Y bounding box of the entire print (all layers)"""
        x_positions = []
        y_positions = []
        
        # Analyze the entire G-code to find all extrusion moves (excluding rapid moves)
        for line in self.base_gcode.splitlines():
            # Only consider G1 moves that are likely extrusion moves (not travel moves)
            if line.startswith("G1 ") and "E" in line:
                x_match = re.search(r'X([0-9]+\.?[0-9]*)', line)
                y_match = re.search(r'Y([0-9]+\.?[0-9]*)', line)
                
                if x_match and y_match:
                    x_positions.append(float(x_match.group(1)))
                    y_positions.append(float(y_match.group(1)))
        
        if x_positions and y_positions:
            min_x = min(x_positions)
            max_x = max(x_positions)
            min_y = min(y_positions)
            max_y = max(y_positions)
            
            print(f"Overall print bounding box: X=[{min_x:.2f}, {max_x:.2f}], Y=[{min_y:.2f}, {max_y:.2f}]")
            print(f"Overall print dimensions: Width={max_x - min_x:.2f}mm, Depth={max_y - min_y:.2f}mm")
            print(f"Overall print center: X={((min_x + max_x)/2):.2f}, Y={((min_y + max_y)/2):.2f}")
            
            return min_x, max_x, min_y, max_y
        else:
            print("Warning: Could not determine print boundaries, using default values")
            return 0, 100, 0, 100

    def get_last_position(self):
        """Get the very last position in the gcode"""
        x, y, z, e = None, None, None, None
        
        for line in self.base_gcode.splitlines():
            if line.startswith("G0 ") or line.startswith("G1 "):
                x_match = re.search(r'X([0-9]+\.?[0-9]*)', line)
                y_match = re.search(r'Y([0-9]+\.?[0-9]*)', line)
                z_match = re.search(r'Z([0-9]+\.?[0-9]*)', line)
                e_match = re.search(r'E([0-9]+\.?[0-9]*)', line)
                
                if x_match:
                    x = float(x_match.group(1))
                if y_match:
                    y = float(y_match.group(1))
                if z_match:
                    z = float(z_match.group(1))
                if e_match:
                    e = float(e_match.group(1))
        
        return x, y, z, e

    def generate_gcode(self):
        # Remove the PRINT_END sequence from base gcode if it exists
        base_gcode_cleaned = self.remove_print_end_sequence().rstrip()
        
        print(f"Starting cylinder at Z={self.start_z:.3f}mm (second-to-last layer)")
        print(f"Cylinder center: X={self.center_x:.2f}, Y={self.center_y:.2f}")
        print(f"Cylinder diameter: {self.cylinder_diameter}mm, Nozzle diameter: {self.nozzle_diameter}mm")
        print(f"Initial flow rate: {self.initial_flow_rate}%, Flow increase per section: {self.flow_increase}%")
        
        # Create continuation G-code
        continuation_gcode = "\n\n; CYLINDER CONTINUATION - SPIRAL VASE MODE\n"
        continuation_gcode += f"; Generated on: 2025-03-05 17:11:09\n"
        continuation_gcode += f"; Generated by: xboxhacker\n"
        continuation_gcode += f"; Starting Z: {self.start_z:.3f} mm (second-to-last layer)\n"
        continuation_gcode += f"; Layer height: {self.layer_height} mm\n"
        continuation_gcode += f"; Section height: {self.section_height} mm\n"
        continuation_gcode += f"; Initial flow rate: {self.initial_flow_rate}%\n"
        continuation_gcode += f"; Bed temperature: {self.bed_temp} °C\n"
        continuation_gcode += f"; Nozzle temperature: {self.nozzle_temp} °C\n"
        continuation_gcode += f"; Flow increase per section: {self.flow_increase}%\n"
        continuation_gcode += f"; Number of sections: {self.num_sections}\n"
        continuation_gcode += f"; Nozzle diameter: {self.nozzle_diameter} mm\n"
        continuation_gcode += f"; Cylinder diameter: {self.cylinder_diameter} mm\n"
        continuation_gcode += f"; Print bounding box: X=[{self.min_x:.2f}, {self.max_x:.2f}], Y=[{self.min_y:.2f}, {self.max_y:.2f}]\n"
        continuation_gcode += f"; Cylinder center: X={self.center_x:.2f}, Y={self.center_y:.2f}\n\n"
        
        # REMOVED as requested: M104, M140
        # RE-ADDED as requested: G90, M83
        
        # Make sure we're in the right modes for vase printing
        continuation_gcode += "G90 ; Absolute positioning\n"
        continuation_gcode += "M83 ; Relative extruder mode\n"
        
        # Set initial flow rate
        continuation_gcode += f"M221 S{self.initial_flow_rate} ; Set initial flow rate to {self.initial_flow_rate}%\n"
        
        # Calculate extrusion parameters
        extrusion_width = self.nozzle_diameter * 1.2
        extrusion_height = self.layer_height
        extrusion_area = extrusion_width * extrusion_height
        filament_area = math.pi * ((1.75/2) ** 2)  # Assuming 1.75mm filament
        extrusion_ratio = extrusion_area / filament_area
        
        # Start at the first point on the perimeter
        radius = self.cylinder_radius
        first_x = self.center_x + radius
        first_y = self.center_y
        
        # Move to the first point of the cylinder and set Z to the starting height
        continuation_gcode += f"; Moving to start position for cylinder perimeter\n"
        continuation_gcode += f"G0 F3000 X{first_x:.3f} Y{first_y:.3f} ; Move to first point\n"
        continuation_gcode += f"G1 F1200 Z{self.start_z:.3f} ; Move to second-to-last layer Z height\n"
        
        # Prime the extruder to ensure good extrusion
        continuation_gcode += f"G1 F300 E5.0 ; Prime extruder for good adhesion\n"
        
        # Print the first perimeter at the starting Z height
        continuation_gcode += f"; Printing first perimeter at Z={self.start_z:.3f} (second-to-last layer)\n"
        
        segments = 72  # Number of segments in a circle (5° per segment)
        for i in range(1, segments + 1):
            angle = (i * 2 * math.pi / segments)
            x = self.center_x + radius * math.cos(angle)
            y = self.center_y + radius * math.sin(angle)
            
            # Calculate length of segment
            prev_x = self.center_x + radius * math.cos((i-1) * 2 * math.pi / segments)
            prev_y = self.center_y + radius * math.sin((i-1) * 2 * math.pi / segments)
            segment_length = math.sqrt((x - prev_x)**2 + (y - prev_y)**2)
            
            # Calculate extrusion amount based on segment length with extra for better adhesion
            # (Flow rate is now controlled by M221 commands, not by manipulating extrusion values)
            extrusion = segment_length * extrusion_ratio * 1.3  # 30% extra for first layer
            
            # Add the point - staying at the exact same Z height
            continuation_gcode += f"G1 F600 X{x:.3f} Y{y:.3f} E{extrusion:.4f}\n"
        
        # Begin the spiral after first full perimeter is complete
        continuation_gcode += f"\n; Beginning spiral climb from Z={self.start_z:.3f}\n"
        
        # Start spiral vase mode
        current_z = self.start_z
        target_z = self.start_z + (self.num_sections * self.section_height)
        current_section = 0
        current_flow_rate = self.initial_flow_rate
        
        # Create a continuous spiral
        z_per_segment = self.layer_height / segments  # Z increase per segment
        
        # Generate the main spiral vase
        steps = int(((target_z - self.start_z) / z_per_segment) + 1)
        for i in range(steps):
            angle = ((i % segments) * 2 * math.pi / segments)
            x = self.center_x + radius * math.cos(angle)
            y = self.center_y + radius * math.sin(angle)
            current_z += z_per_segment
            
            # Check for section change
            section = int((current_z - self.start_z) / self.section_height)
            if section > current_section:
                current_section = section
                # Calculate new flow rate by adding the flow increase percentage
                current_flow_rate = self.initial_flow_rate + (section * self.flow_increase)
                continuation_gcode += f"; Starting section {section+1} with flow rate {current_flow_rate:.1f}%\n"
                continuation_gcode += f"M221 S{current_flow_rate:.1f} ; Set flow rate to {current_flow_rate:.1f}%\n"
            
            # Calculate segment length
            prev_angle = ((i-1) % segments * 2 * math.pi / segments)
            prev_x = self.center_x + radius * math.cos(prev_angle)
            prev_y = self.center_y + radius * math.sin(prev_angle)
            segment_length = math.sqrt((x - prev_x)**2 + (y - prev_y)**2 + z_per_segment**2)
            
            # Calculate extrusion
            extrusion = segment_length * extrusion_ratio
            
            # Add the spiral point
            continuation_gcode += f"G1 X{x:.3f} Y{y:.3f} Z{current_z:.4f} E{extrusion:.4f} F800\n"
            
            # Add layer comment every full revolution
            if (i % segments) == 0 and i > 0:
                layer_num = int((current_z - self.start_z) / self.layer_height)
                continuation_gcode += f"; Layer {layer_num}, Z={current_z:.2f}\n"
                
            # Stop when we reach the target height
            if current_z >= target_z:
                break
        
        # End the print
        continuation_gcode += "\n; End spiral vase cylinder\n"
        
        # If we found a PRINT_END sequence, use it
        if self.print_end_sequence:
            continuation_gcode += "\n" + self.print_end_sequence + "\n"
        else:
            # Otherwise use basic ending commands
            continuation_gcode += "M104 S0 ; Turn off extruder\n"
            continuation_gcode += "M140 S0 ; Turn off bed\n"
            continuation_gcode += "M107 ; Turn off fan\n"
            continuation_gcode += "M84 ; Disable motors\n"
        
        # Combine base G-code with the cylinder G-code
        full_gcode = base_gcode_cleaned + continuation_gcode
        
        return full_gcode

def extract_settings_from_gcode(base_gcode):
    """Try to extract settings from the base gcode file"""
    settings = {
        "layer_height": 0.2,
        "bed_temp": 60,
        "nozzle_temp": 210,
        "initial_flow_rate": 100,  # Now in percentage (%)
        "section_height": 5.0,
        "flow_increase": 10,       # Now in percentage (%)
        "nozzle_diameter": 0.4,
        "cylinder_diameter": 20.0
    }
    
    # Look for commented settings
    for line in base_gcode.splitlines():
        # Check for layer height
        if "layer" in line.lower() and "height" in line.lower():
            match = re.search(r'([0-9]+\.?[0-9]*)\s*mm', line)
            if match:
                settings["layer_height"] = float(match.group(1))
        
        # Check for nozzle diameter
        if "nozzle" in line.lower() and "diameter" in line.lower():
            match = re.search(r'([0-9]+\.?[0-9]*)\s*mm', line)
            if match:
                settings["nozzle_diameter"] = float(match.group(1))
                
        # Check for temperatures
        if "bed" in line.lower() and "temp" in line.lower():
            match = re.search(r'([0-9]+\.?[0-9]*)', line)
            if match:
                settings["bed_temp"] = int(float(match.group(1)))
                
        if "nozzle" in line.lower() and "temp" in line.lower() or "hotend" in line.lower():
            match = re.search(r'([0-9]+\.?[0-9]*)', line)
            if match:
                settings["nozzle_temp"] = int(float(match.group(1)))
                
        # Look for flow rate settings (M221)
        if line.startswith("M221 "):
            match = re.search(r'S([0-9]+\.?[0-9]*)', line)
            if match:
                settings["initial_flow_rate"] = int(float(match.group(1)))
    
    # Look for actual M104/M140 commands for temperatures
    for line in base_gcode.splitlines():
        if line.startswith("M140"):
            match = re.search(r'S([0-9]+\.?[0-9]*)', line)
            if match:
                settings["bed_temp"] = int(float(match.group(1)))
        
        if line.startswith("M104") or line.startswith("M109"):
            match = re.search(r'S([0-9]+\.?[0-9]*)', line)
            if match:
                settings["nozzle_temp"] = int(float(match.group(1)))
                
        # Look for M221 flow rate commands
        if line.startswith("M221"):
            match = re.search(r'S([0-9]+\.?[0-9]*)', line)
            if match:
                settings["initial_flow_rate"] = int(float(match.group(1)))
    
    return settings

def get_layer_heights(base_gcode):
    """Find all unique layer heights in the gcode file"""
    z_heights = set()
    
    for line in base_gcode.splitlines():
        if line.startswith("G0 ") or line.startswith("G1 "):
            z_match = re.search(r'Z([0-9]+\.?[0-9]*)', line)
            if z_match:
                z = float(z_match.group(1))
                z_heights.add(z)
    
    return sorted(list(z_heights))

def create_gcode_file(base_gcode, layer_height, section_height, initial_flow_rate, bed_temp, nozzle_temp, 
                     flow_increase, num_sections, nozzle_diameter, cylinder_diameter):
    try:
        generator = GCodeGenerator(base_gcode, layer_height, section_height, initial_flow_rate, bed_temp, 
                                  nozzle_temp, flow_increase, num_sections, nozzle_diameter, cylinder_diameter)
        gcode = generator.generate_gcode()
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output.gcode")
        with open(output_path, "w") as file:
            file.write(gcode)
        print(f"G-code file generated successfully at: {output_path}")
        print(f"File size: {os.path.getsize(output_path)/1024:.1f} KB")
        messagebox.showinfo("Success", f"G-code file generated successfully!\nLocation: {output_path}")
        return True
    except Exception as e:
        print(f"Error generating G-code: {e}")
        messagebox.showerror("Error", f"Error generating G-code: {e}")
        return False

def main():
    try:
        root = tk.Tk()
        root.title("Belt Printer Flow Cylinder Generator")
        
        # Set window size
        root.geometry("500x520")
        
        # Create a frame with better styling
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Load base gcode file
        try:
            base_gcode_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base.gcode")
            if not os.path.exists(base_gcode_path):
                raise FileNotFoundError("base.gcode file not found in the script directory.")

            with open(base_gcode_path, "r") as file:
                base_gcode = file.read()
                
            # Extract default values from gcode
            settings = extract_settings_from_gcode(base_gcode)
            
            # Get layer heights
            layer_heights = get_layer_heights(base_gcode)
            if len(layer_heights) >= 2:
                second_last_z = layer_heights[-2]
                print(f"DEBUG: Second-to-last layer Z={second_last_z:.3f}")
            else:
                second_last_z = 0
                
        except Exception as e:
            print(f"Error loading base.gcode: {e}")
            messagebox.showerror("Error", f"Error loading base.gcode: {e}")
            return
        
        # Create form with labels and entry boxes using ttk for better styling
        ttk.Label(main_frame, text="G-Code Parameters", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")
        
        # Display cylinder start Z information - removed "(second-to-last layer)" text
        row = 1
        ttk.Label(main_frame, text="Cylinder Start Z:", font=("Arial", 10, "bold")).grid(row=row, column=0, sticky="w")
        ttk.Label(main_frame, text=f"{second_last_z:.3f} mm", foreground="#009900").grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        
        row += 1
        ttk.Label(main_frame, text="Layer Height (mm):").grid(row=row, column=0, sticky="w")
        layer_height_var = tk.DoubleVar(value=settings["layer_height"])
        ttk.Entry(main_frame, textvariable=layer_height_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Label(main_frame, text="Section Height (mm):").grid(row=row, column=0, sticky="w")
        section_height_var = tk.DoubleVar(value=settings["section_height"])
        ttk.Entry(main_frame, textvariable=section_height_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Label(main_frame, text="Initial Flow Rate (%):").grid(row=row, column=0, sticky="w")
        initial_flow_rate_var = tk.IntVar(value=settings["initial_flow_rate"])
        ttk.Entry(main_frame, textvariable=initial_flow_rate_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Label(main_frame, text="Bed Temperature (°C):").grid(row=row, column=0, sticky="w")
        bed_temp_var = tk.IntVar(value=settings["bed_temp"])
        ttk.Entry(main_frame, textvariable=bed_temp_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Label(main_frame, text="Nozzle Temperature (°C):").grid(row=row, column=0, sticky="w")
        nozzle_temp_var = tk.IntVar(value=settings["nozzle_temp"])
        ttk.Entry(main_frame, textvariable=nozzle_temp_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Label(main_frame, text="Flow Increase per Section (%):").grid(row=row, column=0, sticky="w")
        flow_increase_var = tk.IntVar(value=settings["flow_increase"])
        ttk.Entry(main_frame, textvariable=flow_increase_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Label(main_frame, text="Number of Sections:").grid(row=row, column=0, sticky="w")
        num_sections_var = tk.IntVar(value=1)
        ttk.Entry(main_frame, textvariable=num_sections_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Label(main_frame, text="Nozzle Diameter (mm):").grid(row=row, column=0, sticky="w")
        nozzle_diameter_var = tk.DoubleVar(value=settings["nozzle_diameter"])
        ttk.Entry(main_frame, textvariable=nozzle_diameter_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Label(main_frame, text="Cylinder Diameter (mm):").grid(row=row, column=0, sticky="w")
        cylinder_diameter_var = tk.DoubleVar(value=settings["cylinder_diameter"])
        ttk.Entry(main_frame, textvariable=cylinder_diameter_var, width=10).grid(row=row, column=1, pady=5, padx=10, sticky="w")
        
        row += 1
        ttk.Separator(main_frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        
        row += 1
        # Button to generate G-code
        generate_button = ttk.Button(
            main_frame, 
            text="Generate G-code",
            command=lambda: create_gcode_file(
                base_gcode,
                layer_height_var.get(),
                section_height_var.get(),
                initial_flow_rate_var.get(),
                bed_temp_var.get(),
                nozzle_temp_var.get(),
                flow_increase_var.get(),
                num_sections_var.get(),
                nozzle_diameter_var.get(),
                cylinder_diameter_var.get()
            )
        )
        generate_button.grid(row=row, column=0, columnspan=2, pady=15)
        
        # Display base.gcode file info
        row += 1
        file_info = f"Using base.gcode: {base_gcode_path}\nFile size: {os.path.getsize(base_gcode_path)/1024:.1f} KB"
        ttk.Label(main_frame, text=file_info, foreground="gray").grid(row=row, column=0, columnspan=2, pady=(5, 5), sticky="w")
        
        # Center the window
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'+{x}+{y}')
        
        root.mainloop()
        
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    main()
