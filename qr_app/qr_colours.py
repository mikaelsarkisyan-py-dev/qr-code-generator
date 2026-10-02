# code written by Mikael

from tkinter.messagebox import showwarning


PRESETS = {
    "Standard (Recommended)": {
        "fg": "#000000",
        "bg": "#FFFFFF",
        "scale": 10,
        "invert": False,
        "desc": "Best overall option. High contrast and reliable on all scanners."
    },
    "High Contrast (Low Vision)": {
        "fg": "#000000",
        "bg": "#FFD700",
        "scale": 14,
        "invert": False,
        "desc": "Large QR code with strong contrast for poor eyesight."
    },
    "Colour-blind": {
        "fg": "#0033CC",
        "bg": "#FFFFFF",
        "scale": 12,
        "invert": False,
        "desc": "Blue on white avoids red/green confusion."
    }
}


def _luminance(hex_colour):
    hex_colour = hex_colour.lstrip("#")
    r, g, b = [int(hex_colour[i:i+2], 16) / 255 for i in (0, 2, 4)]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast_ratio(fg, bg):
    l1 = _luminance(fg)
    l2 = _luminance(bg)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def show_accessibility_warnings(fg, bg, inverted=False):
    ratio = contrast_ratio(fg, bg)

    if ratio < 3:
        showwarning(
            "Low Contrast Warning",
            "The selected colours have low contrast.\n"
            "This may be difficult to scan, especially on older devices."
        )

    if inverted:
        showwarning(
            "Inversion Warning",
            "Inverted QR codes may not scan correctly on some devices."
        )
