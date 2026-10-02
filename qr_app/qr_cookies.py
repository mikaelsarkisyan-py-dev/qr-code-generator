# Team project

import tkinter as tk
import tkinter.font as tkfont
import sys

class QRCodeCookies:
    def __init__(self, root):
        self.root = root

        for font_name in ("TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont"):
            tkfont.nametofont(font_name).configure(size=12)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.title("QR Code App EULA")
        self.root.geometry("640x760")
        self.root.resizable(False, True)

        EULA = """
    QR Code App EULA


    1. Data Collection and Data Usage

    This application respects user privacy and follows core data protection principles.


    What data is collected?

    - This application does not collect personal data unless provided by the user.

    - Any data entered (e.g. text for QR code generation) is processed locally on your
    device.

    - No information is transmitted to external servers unless clearly stated.


    How is data used?

    - User input is used only to perform the requested function (e.g. generating a QR code,
    reading a QR code).

    - All data is stored locally on your device (e.g. generated QR codes, analytics data).

    - Temporary data is cleared when the application is closed.


    2. Security and Risk Awareness

    QR Code Safety Warning:

    - QR codes can link to websites, files, or commands that may be unsafe.

    Users should be aware that:

    - QR codes can be used in phishing scams.

    - Scanning unknown QR codes may lead to malicious websites.

    - Sensitive information should never be encoded in QR codes.

    - This application does not verify the safety of external links contained in QR codes.
    
    - Users are responsible for checking the legitimacy of content before scanning or
    sharing QR codes.


    3. Information Modelling and System Design

    How information is modelled:

    - User data is structured using appropriate data types (e.g., strings, integers).

    - Input values are validated before processing.

    - Application logic is separated into clear components (e.g., input handling, processing,
    display).

    
    Managing user input

    To ensure reliability and security, the application:

    - Validates input to prevent invalid or harmful data.

    - Provides clear error messages when input is incorrect.

    - Guides users with instructions and prompts.

    
    Data integrity and security

    The application ensures data integrity by:

    - Preventing crashes through error handling (try/except).

    - Avoiding unsafe operations on user input.

    - Ensuring consistent data processing.

    - Limiting access to sensitive operations.

    
    Error handling:

    - Errors are caught and handled gracefully.

    - Users receive understandable feedback instead of technical error messages.

    - The application prevents data corruption by stopping unsafe operations.

    
    4. User Responsibility

    Users should:

    - Avoid entering sensitive or personal information into QR codes.

    - Be cautious when scanning QR codes from unknown sources.

    - Use the application responsibly and securely.


    By clicking "Accept", you understand and agree to the terms outlined in this EULA
    regarding data usage, security, and user responsibility.

    """

        self.text = tk.Text(self.root, wrap=tk.WORD, font=("Arial", 12), padx=10, pady=8)
        self.text.pack(expand=True, fill=tk.BOTH)
        self.text.insert(tk.END, EULA)
        self.text.config(state="disabled")

        self.accept_button = tk.Button(self.root, text="Accept", bg='#99ff99', command=self.accept)
        self.accept_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.deny_button = tk.Button(self.root, text="Deny", bg='#ff9999', command=self.on_close)
        self.deny_button.pack(side=tk.RIGHT, padx=10, pady=10)

    def accept(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.quit()
        with open("eula_accepted.txt", "w") as f:
            f.write("1")

    def on_close(self):
        self.root.quit()
        self.root.destroy()
        with open("eula_accepted.txt", "w") as f:
            f.write("0")
        sys.exit()
