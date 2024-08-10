import tkinter as tk
from tkinter import font

root = tk.Tk()

# Get list of available font families
available_fonts = font.families()

# Print the available font families
for f in available_fonts:
    print(f)

root.destroy()
