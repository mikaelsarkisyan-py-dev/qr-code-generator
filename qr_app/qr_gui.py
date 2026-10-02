# Team project; GUI and accessibility features by Mikael

from qr_encode import makeBitstream
from qr_matrix import generateQRMatrix
from qr_colours import PRESETS, show_accessibility_warnings
from qr_reader_decode import decodeQrCode
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import ListedColormap
import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
from tkinter.messagebox import showerror, showinfo
import tkinter.font as tkfont
import sys
import time
import os
import numpy as np
from qr_analytics_logger import (
    log_qr_generation,
    show_ecl_frequency,
    show_success_failure_over_time,
    clear_logs
)

# GUI Application for QR Code Generation
class QRApp:
    def __init__(self, root):
        # Initialize main window
        self.root = root

        for font_name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont"):
            tkfont.nametofont(font_name).configure(size=12)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.title("QR Code App")
        self.root.geometry("660x860")
        self.root.resizable(False, False)

        # Default colours
        self.fg_colour = "#000000"
        self.bg_colour = "#FFFFFF"
        self.setup_tabs(self.root)

    # Create tabs for generator and reader
    def setup_tabs(self, root):
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        gen_tab = self.setup_generator_ui(notebook)
        read_tab = self.setup_reader_ui(notebook)
        analytics_tab = self.setup_analytics_ui(notebook)
        help_tab = self.setup_help_ui(notebook)

        notebook.add(gen_tab, text="Generate QR")
        notebook.add(read_tab, text="Read QR")
        notebook.add(analytics_tab, text="Analytics")
        notebook.add(help_tab, text="Help / About")

    # Setup QR code generator UI
    def setup_generator_ui(self, parent):
        # Input
        frame = ttk.Frame(parent)
        tk.Label(frame, text="Enter text to encode:").pack(pady=5)
        self.entry = tk.Entry(frame, width=45)
        self.entry.pack()

        # QR Level selector
        tk.Label(frame, text="QR Code Version:").pack(pady=5)
        self.level_var = tk.StringVar(value="Automatic")
        self.level_list = ["Automatic", "Version 1", "Version 2"]
        tk.OptionMenu(
            frame, self.level_var, *self.level_list
        ).pack()

        # QR ECL selector
        tk.Label(frame, text="QR Code Error Correction Level:").pack(pady=5)
        self.ecl_var = tk.StringVar(value="Automatic")
        self.ecl_list = ["Automatic", "L", "M", "Q", "H"]
        tk.OptionMenu(
            frame, self.ecl_var, *self.ecl_list
        ).pack()

        self.level_var.trace_add("write", lambda *args: self.recalculate_length())
        self.ecl_var.trace_add("write", lambda *args: self.recalculate_length())

        # Custom QR description
        self.custom_qr = tk.Label(frame, wraplength=500, justify="left")
        self.custom_qr.pack(pady=5)
        self.recalculate_length()

        # Presets
        tk.Label(frame, text="Accessibility Preset:").pack(pady=5)
        self.preset_var = tk.StringVar(value="Standard (Recommended)")
        tk.OptionMenu(
            frame, self.preset_var, *PRESETS.keys(), command=self.apply_preset
        ).pack()

        # Preset description
        self.desc_label = tk.Label(frame, wraplength=500, justify="left")
        self.desc_label.pack(pady=5)
        self.apply_preset(self.preset_var.get())

        # Colour picker
        tk.Label(frame, text="Custom QR Colour (Advanced):").pack(pady=5)
        tk.Button(
            frame,
            text="Choose QR Colour",
            command=self.pick_colour
        ).pack()

        # Generate button
        self.generate_button = tk.Button(frame, text="Generate QR Code", bg='#99ff99', command=self.create_qr)
        self.generate_button.pack()

        # Matplotlib figure for displaying QR code
        self.fig, self.ax = plt.subplots(dpi=150)
        self.ax.axis('off') # hide axis labels
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.get_tk_widget().pack()

        return frame
    
    # Setup QR code reader UI
    def setup_reader_ui(self, parent):
        frame = ttk.Frame(parent)
        tk.Label(frame, text="Upload QR Code Image:").pack(pady=5)
        self.upload_button = tk.Button(frame, text="Browse", command=self.browse_image)
        self.upload_button.pack()

        self.image_name_label = tk.Label(frame, text="No image selected")
        self.image_name_label.pack(pady=5)

        self.image_label = tk.Label(frame)
        self.image_label.pack(pady=5)

        self.read_button = tk.Button(frame, text="Read QR Code", command=self.read_qr_code)
        self.read_button.pack()

        self.result_label = tk.Label(frame, wraplength=500, justify="left")
        self.result_label.pack(pady=5)

        return frame

    def browse_image(self):
        file_path = filedialog.askopenfilename(
            initialdir="generated_codes",
            title="Select QR Code Image",
            filetypes=[("Image Files", "*.png;*.bmp;*.gif")]
        )

        if not file_path:
            return
        
        file_name = os.path.basename(file_path)
        self.image_name_label.config(text=file_name)

        img = tk.PhotoImage(file=file_path)
        if img.width() > 256 or img.height() > 256:
            width = int(img.width()/256)
            height = int(img.height()/256)
            img = img.subsample(width, height)
        else:
            width = int(256/img.width())
            height = int(256/img.height())
            img = img.zoom(width, height)
        self.image_label.config(image=img)
        self.image_label.image = img
        self.file_path = file_path
            
    def read_qr_code(self):
        if not hasattr(self, 'file_path'):
            showerror("Error", message="No image selected!")
            return
        
        img = mpimg.imread(self.file_path)

        try:
            data = decodeQrCode(img)
            self.result_label.config(text=f"Decoded Data:\n{data}")
        except Exception as err:
            showerror("Error", message=str(err))
            return

    def setup_analytics_ui(self, parent):
        frame = ttk.Frame(parent)

        tk.Button(
            frame,
            text="Show ECC Usage Frequency",
            command=show_ecl_frequency
        ).pack(pady=10)

        tk.Button(
            frame,
            text="Show Success vs Failure Over Time",
            command=show_success_failure_over_time
        ).pack(pady=10)

        tk.Button(
            frame,
            text="Clear CSV Log",
            command=clear_logs
        ).pack(pady=10)

        return frame
    
    def setup_help_ui(self, parent):
        frame = ttk.Frame(parent)

        help_text = """
    QR Code Generator and Reader Application

    This application allows you to generate QR codes with customizable options, read
    QR codes from images, and view analytics on QR code generation.

    Features:
    - Generate QR codes with different versions and error correction levels.
    - Choose accessibility presets for better visibility.
    - Customize QR code colors.
    - Read QR codes from image files.
    - View analytics on QR code generation success rates and error correction usage.

    How to generate a QR code:
    1. Enter the text you want to encode into the QR code.
    2. Select the desired QR code version and error correction level (Automatic selects
    the best option for the given input).
    3. Choose an accessibility preset or customize the QR code color.
    4. Click "Generate QR Code" to create and display the QR code. The QR code will
    also be saved as a PNG file in the "generated_codes" folder.

    How to read a QR code:
    1. Click "Browse" to select a QR code image file from your computer. (Note: only QR
    codes generated by this applications are supported, but other QR codes may work if
    set to the correct size).
    2. Click "Read QR Code" to decode the QR code and display the encoded text.

    Analytics:
    - View the frequency of error correction levels used in generated QR codes.
    - View success vs failure rates of QR code generation over time.
    - Clear the CSV log of QR code generation data.
    """

        label = tk.Label(frame, text=help_text, wraplength=600, justify="left")
        label.pack(pady=10, padx=10)

        return frame

    # ------------------------------
    # Apply level selector
    # ------------------------------
    def recalculate_length(self):
        qr_version = self.level_var.get()
        ecl = self.ecl_var.get()
        codewordDict = {
            ('Version 1', 'L'): 19,
            ('Version 1', 'M'): 16,
            ('Version 1', 'Q'): 13,
            ('Version 1', 'H'): 9,
            ('Version 2', 'L'): 34,
            ('Version 2', 'M'): 28,
            ('Version 2', 'Q'): 22,
            ('Version 2', 'H'): 16
        }
        if qr_version == "Automatic" and ecl == "Automatic":
            self.custom_qr.config(text = "Maximum characters: " + str(codewordDict[('Version 2', 'L')]-2))
        elif qr_version != "Automatic" and ecl == "Automatic":
            self.custom_qr.config(text = "Maximum characters: " + str(codewordDict[(qr_version, 'L')]-2))
        elif qr_version == "Automatic" and ecl != "Automatic":
            self.custom_qr.config(text = "Maximum characters: " + str(codewordDict[('Version 2', ecl)]-2))
        else:
            self.custom_qr.config(text = "Maximum characters: " + str(codewordDict[(qr_version, ecl)]-2))

    # ------------------------------
    # Apply preset
    # ------------------------------
    def apply_preset(self, preset_name):
        preset = PRESETS[preset_name]
        self.fg_colour = preset["fg"]
        self.bg_colour = preset["bg"]
        self.scale = preset["scale"]
        self.invert = preset["invert"]
        self.desc_label.config(text=f"Preset explanation:\n{preset['desc']}")
    
    # ------------------------------
    # Colour picker
    # ------------------------------
    def pick_colour(self):
        colour = colorchooser.askcolor(title="Select QR Colour")
        if colour[1]:
            self.fg_colour = colour[1]

    # ------------------------------
    # Create QR code from input data called after generate button pressed
    # ------------------------------
    def create_qr(self):
        dataIn = self.entry.get().strip()
        lvlIn = self.level_var.get()
        eclIn = self.ecl_var.get()

        lvlDict = {
            "Automatic": 0,
            "Version 1": 1,
            "Version 2": 2
        }
        eclDict = {
            "Automatic": 0,
            "L": 'L',
            "M": 'M',
            "Q": 'Q',
            "H": 'H'
        }

        try:
            bitstream, version, ecl = makeBitstream(
                dataIn,
                lvlDict[lvlIn],
                eclDict[eclIn]
            )

            qrMatrix, mask_pattern = generateQRMatrix(version, bitstream, ecl)

            if self.invert:
                qrMatrix = 1 - qrMatrix

            qrMatrix = (qrMatrix > 0).astype(int)

            quiet_zone = 4
            qrMatrix = np.pad(
                qrMatrix,
                pad_width=quiet_zone,
                mode="constant",
                constant_values=0
            )

            show_accessibility_warnings(
                self.fg_colour,
                self.bg_colour,
                inverted=self.invert
            )

            self.fig.clf()
            self.ax = self.fig.add_subplot(111)

            self.fig.patch.set_facecolor(self.bg_colour)
            self.ax.set_facecolor(self.bg_colour)
            self.canvas.get_tk_widget().config(bg=self.bg_colour)

            self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

            qr_cmap = ListedColormap([self.bg_colour, self.fg_colour])

            self.ax.imshow(qrMatrix, cmap=qr_cmap, interpolation="nearest")
            self.ax.axis("off")
            self.canvas.draw()

            time_save = int(time.time()*1000000)
            try:
                os.makedirs("generated_codes", exist_ok=True)
            except Exception:
                pass
            
            mpimg.imsave(
                f"generated_codes/qr_code_{time_save}.png",
                qrMatrix,
                cmap=qr_cmap
            )

            # LOG SUCCESS
            log_qr_generation(
                text_content=dataIn,
                version=version,
                ecl=ecl,
                mask_pattern=mask_pattern,
                user_options={
                    "preset": self.preset_var.get(),
                    "fg_colour": self.fg_colour,
                    "bg_colour": self.bg_colour,
                    "scale": self.scale
                },
                inverted=self.invert,
                success=True
            )

            showinfo(
                "Success",
                message=f"QR Code generated successfully!\n"
                        f"Version: {version}, Error Correction Level: {ecl}\n"
                        f"Saved as: qr_code_{time_save}.png"
            )

        except Exception as err:
        # LOG FAILURE
            log_qr_generation(
                text_content=dataIn,
                version=None,
                ecl=None,
                mask_pattern=None,
                user_options={
                    "preset": self.preset_var.get()
                },
                inverted=self.invert,
                success=False
            )
            showerror("Error", message=str(err))
            return

    def on_close(self):
        plt.close(self.fig)
        self.root.quit()
        self.root.destroy()
        sys.exit()