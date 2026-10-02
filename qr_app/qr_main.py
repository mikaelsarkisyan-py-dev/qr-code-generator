# Team project

from qr_gui import QRApp
from qr_cookies import QRCodeCookies
import tkinter as tk

# Function to check if eula has been accepted
def accepted():
    try:
        with open("eula_accepted.txt", "r") as f:
            return f.read().strip() == "1"
    except FileNotFoundError:
        return False

root = tk.Tk()

# Initial check
if accepted():
    qr_app = QRApp(root)
    root.mainloop()
else:
    cookies = QRCodeCookies(root)
    root.mainloop()

# Run app if eula accepted
if accepted():
    qr_app = QRApp(root)
    root.mainloop()
