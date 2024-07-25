import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import socket
import struct
import os
from dotenv import load_dotenv
from threading import Thread
import picommand
import io
import platform
import subprocess
import asyncio
import threading
import multiprocessing
from multiprocessing import Process
import time

# Load environment
load_dotenv()

host_name = os.getenv('HOSTNAME')
port = int(os.getenv("PORT"))
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
raspberry_ip = os.getenv("RASPI_IP")


stream_status = False
con_status = "unchecked"


async def ping_connection(ip_address):
    param = '-n' if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "1", ip_address]

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error while pinging: {e}")
        return False


def run_async_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def check_connection():
    log_console(f"Check Connection {raspberry_ip}")
    loop = asyncio.new_event_loop()
    threading.Thread(target=run_async_loop, args=(loop,), daemon=True).start()

    async def ping_and_log():
        result = await ping_connection(raspberry_ip)
        status_message = f"{raspberry_ip} is reachable." if result else f"{raspberry_ip} is not reachable."
        log_console(status_message)

    asyncio.run_coroutine_threadsafe(ping_and_log(), loop)


def start_stream():
    global stream_status
    stream_status = True
    if stream_status:
        Thread(target=update_video_image).start()


def stop_stream():
    global stream_status
    stream_status = False


def robot_start_stream():
    p = Process(target=robot_start_stream_command, args=())
    p.start()


def robot_start_stream_command():
    command = picommand.start_stream()
    picommand.ssh_command(host_name, port, username, password, command)


def update_video_image():
    # Set up the client socket
    global raspberry_ip
    raspi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        log_console(f"Try to connect to raspberry pi ip {raspberry_ip}")
        raspi_socket.connect((raspberry_ip, 8080))
        connection = raspi_socket.makefile('rb')
    except Exception as e:
        log_console(f"Error : \n  {e }")

    global stream_status
    while stream_status:
        try:
            image_len = struct.unpack(
                '<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                continue

            # read image data
            image_data = connection.read(image_len)
            image = Image.open(io.BytesIO(image_data))

            # convert the image to a format Tkinter can display
            tk_image = ImageTk.PhotoImage(image)

            label.config(image=tk_image)
            label.image = tk_image  # Keep a reference to avoid garbage collection
        except Exception as e:
            print("Error receiving image: ", e)
            log_console(f"Error : \n  {e }")
            break

        # Update every 100ms
        time.sleep(0.1)


def run_motor_command(time, dir_code, log_console):
    command = picommand.motor_run_command(time, dir_code)
    picommand.ssh_command(host_name, port, username, password, command)


def run_motor():
    check_val = motor_scale.get()
    if check_val > 0:
        dir_code = 0
        log_console(f"Run Motor forward {check_val}")
    else:
        dir_code = 1
        log_console(f"Run Motor backward {check_val}")
    time = abs(check_val)
    p = Process(target=run_motor_command, args=(time, dir_code, log_console))
    p.start()


def run_servo_command(angle, servo_code):
    command = picommand.run_servo_command(angle, servo_code)
    picommand.ssh_command(host_name, port, username, password, command)


def run_motor_left_right():
    degree_servo = camera_left_right_scale.get()
    servo_code = 1
    if degree_servo < 0:
        log_console(f"Run servo left {degree_servo} code {servo_code}")
    else:
        log_console(f"Run servo right {degree_servo} code {servo_code}")
    angle = abs(degree_servo)
    p = Process(target=run_servo_command, args=(angle, servo_code))
    p.start()


def run_motor_up_down():
    degree_servo = camera_up_down_scale.get()
    servo_code = 2
    if degree_servo < 0:
        log_console(f"Run servo down {degree_servo} code {servo_code}")
    else:
        log_console(f"Run servo up {degree_servo} code {servo_code}")
    angle = abs(degree_servo)
    p = Process(target=run_servo_command, args=(angle, servo_code))
    p.start()


def log_console(message):
    console_text.configure(state='normal')
    console_text.insert(tk.END, message + '\n')
    console_text.configure(state='disabled')
    console_text.yview(tk.END)


def click_update_status():
    update_status("ON", "ON", "ON")


def update_status(con_stat, bat_stat, robot_stat):
    status = (f"Connection status: {con_stat}\n"
              f"Battery condition: {bat_stat}\n"
              f"Robot status: {robot_stat}")

    # Clear existing text
    connection_status_text.config(state=tk.NORMAL)
    connection_status_text.delete(1.0, tk.END)

    # Update the text widget with the new status
    connection_status_text.insert(tk.END, status)

    # Make the text widget uneditable again
    connection_status_text.config(state=tk.DISABLED)


def main():
    global label, console_text, motor_scale, camera_left_right_scale, camera_up_down_scale, con_status, connection_status_text

    root = tk.Tk()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}")
    root.title("Robot Pipeline Inspection V1")

    # Creating Empty Image
    frame_width, frame_height = 640, 480  # Match the actual frame size
    default_image = Image.new(
        'RGBA', (frame_width, frame_height), (255, 255, 255, 255))
    default_photo_image = ImageTk.PhotoImage(default_image)

    # Status Section
    # status_section = tk.Frame(
    #     root, highlightbackground="blue", highlightthickness=2)
    # status_section.pack(side=tk.LEFT, expand=True)

    # status_title = tk.Label(status_section, text="Robot Control Configuration",
    #                         highlightbackground="blue", highlightthickness=2)
    # status_title.grid(column=0, row=0, columnspan=3)

    # Video Section
    video_section = tk.Frame(
        root, highlightbackground="green", highlightthickness=2)
    video_section.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    status_title = tk.Label(video_section, text="Robot Status",
                            highlightbackground="blue", highlightthickness=2)
    status_title.pack(side=tk.TOP)

    default_text = (
        "Connection status : unchecked\n"
        "Battery condition : unchecked\n"
        "Robot status      : unchecked"
    )
    connection_status_text = tk.Text(video_section, height=5, width=52)
    connection_status_text.pack(side=tk.TOP)
    connection_status_text.insert(tk.END, default_text)
    connection_status_text.config(state=tk.DISABLED)

    label = tk.Label(video_section, highlightbackground="orange",
                     highlightthickness=2, image=default_photo_image)
    label.pack(side=tk.TOP)

    stream_section = tk.Frame(
        video_section, highlightbackground="blue", highlightthickness=2)
    stream_section.pack()

    btn_start_stream = tk.Button(
        stream_section, text="Start Stream", command=start_stream)
    btn_start_stream.grid(column=0, row=0)

    btn_stop_stream = tk.Button(
        stream_section, text="Stop Stream", command=stop_stream)
    btn_stop_stream.grid(column=1, row=0)

    btn_check_con = tk.Button(
        stream_section, text="Check Connection", command=check_connection)
    btn_check_con.grid(column=2, row=0)

    btn_start_robot_stream = tk.Button(
        stream_section, text="Start Robot Stream", command=robot_start_stream)
    btn_start_robot_stream.grid(column=3, row=0)

    btn_check_stat = tk.Button(
        stream_section, text="check stat", command=click_update_status)
    btn_check_stat.grid(column=4, row=0)

    control_frame = tk.Frame(
        root, highlightbackground="red", highlightthickness=2)
    control_frame.pack(pady=20)

    control_frame.rowconfigure(1)
    control_frame.columnconfigure(2)

    title_control = tk.Label(control_frame, text="Robot Control Configuration",
                             highlightbackground="blue", highlightthickness=2)
    title_control.grid(column=0, row=0, columnspan=3)

    motor_distance_frame = tk.Frame(
        control_frame, highlightbackground="blue", highlightthickness=2)
    motor_distance_frame.grid(column=1, row=1)

    motor_scale = tk.Scale(
        motor_distance_frame, label="Distance", orient="vertical", from_=10, to=-10)
    motor_scale.grid(column=1, row=1, rowspan=2)

    btn_up = tk.Button(motor_distance_frame,
                       text="Run Motor", command=run_motor)
    btn_up.grid(column=2, row=1)

    servo_frame = tk.Frame(
        control_frame, highlightbackground="blue", highlightthickness=2)
    servo_frame.grid(column=2, row=1)

    camera_up_down_scale = tk.Scale(
        servo_frame, label="Degree", orient="vertical", from_=0, to=180)
    camera_up_down_scale.grid(column=1, row=1, rowspan=2)

    btn_camera_up = tk.Button(
        servo_frame, text="Camera Up/Down", command=run_motor_up_down)
    btn_camera_up.grid(column=2, row=1, rowspan=2, padx=20)

    camera_left_right_scale = tk.Scale(
        servo_frame, label="Degree", orient="horizontal", from_=0, to=180)
    camera_left_right_scale.grid(column=1, row=3, rowspan=2)

    btn_camera_left = tk.Button(
        servo_frame, text="Camera Left/Right", command=run_motor_left_right)
    btn_camera_left.grid(column=2, row=3, rowspan=2, padx=20)

    console_text = scrolledtext.ScrolledText(root, height=10)
    console_text.pack(fill="x", padx=10, pady=10)
    console_text.configure(state='disabled')

    root.mainloop()


if __name__ == '__main__':
    main()
