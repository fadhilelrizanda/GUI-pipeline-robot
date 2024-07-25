import tkinter as tk
from PIL import Image, ImageTk
import socket
import struct
import numpy as np
import io

# Set up the client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.200.2', 8000))
connection = client_socket.makefile('rb')

# Create the Tkinter window
root = tk.Tk()
root.title("Raspberry Pi Camera Stream")

# Create a label to display the video frames
label = tk.Label(root)
label.pack()


def update_frame():
    try:
        # Read the size of the image
        image_len = struct.unpack(
            '<L', connection.read(struct.calcsize('<L')))[0]
        if not image_len:
            return

        # Read the image data
        image_data = connection.read(image_len)
        image = Image.open(io.BytesIO(image_data))

        # Convert the image to a format Tkinter can display
        tk_image = ImageTk.PhotoImage(image)
        label.config(image=tk_image)
        label.image = tk_image
    except Exception as e:
        print("Error receiving image: ", e)

    # Schedule the next frame update
    root.after(100, update_frame)


# Start the video stream
update_frame()
root.mainloop()

# Close the connection
connection.close()
client_socket.close()
