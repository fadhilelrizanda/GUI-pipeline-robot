import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import socket
import struct
import os
from dotenv import load_dotenv
from threading import Thread
import command
import io
import platform
import subprocess
import asyncio
import threading
import multiprocessing
from multiprocessing import Process, Queue
import time

# Load environment
load_dotenv()

host_name = os.getenv('HOSTNAME_ROBOT')
port = int(os.getenv("PORT"))
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
raspberry_ip = os.getenv("RASPI_IP")

stream_status = False
con_status = "unchecked"
keybind_stat = False
picommand = command.Picommand(
    host_name, port, username, password, raspberry_ip)

Ttl_distance = 0
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def check_status():
    log_console("Checking Status ....")
    loading_message = show_loading_message()
    con_status = picommand.check_connection()
    print(con_status)
    if con_status:
        con_status = "ON"
    else:
        con_status = "OFF"
    batt_status = picommand.check_voltage()
    if batt_status == "throttled=0x0":
        batt_status = "Normal"
    print(batt_status)
    log_console(f"Connection Status : {con_status}")
    log_console(f"Battery Status : {batt_status}")
    update_status(con_status, batt_status)
    loading_message.destroy()


def start_stream():
    global stream_status
    stream_status = True
    if stream_status:
        Thread(target=update_video_image).start()


def stop_stream():
    global stream_status
    stream_status = False


def robot_start_stream_trig():
    loading_message = show_loading_message()
    queue = Queue()
    p = Process(target=picommand.start_stream, args=(queue,))

    def wait_for_process():
        p.start()
        log_console(f"Starting stream ...")
        p.join()
        result = queue.get()
        log_console(result)
        loading_message.destroy()
    Thread(target=wait_for_process).start()


def update_video_image():
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

            image_data = connection.read(image_len)
            image = Image.open(io.BytesIO(image_data))

            tk_image = ImageTk.PhotoImage(image)

            label.config(image=tk_image)
            label.image = tk_image
        except Exception as e:
            print("Error receiving image: ", e)
            log_console(f"Error : \n  {e }")
            break

        time.sleep(0.1)


def run_motor_trig():
    global Ttl_distance
    loading_message = show_loading_message()
    check_val = int(sp_motor.get())
    check_motor_type = radio_var.get()
    Ttl_distance += check_val
    update_distance(Ttl_distance)
    print(check_motor_type)
    queue = Queue()
    p = Process(target=picommand.motor_run_command,
                args=(check_val, check_motor_type, queue))

    def wait_for_process():
        p.start()
        log_console(f"Run motor {check_val} cm")
        p.join()
        result = queue.get()
        log_console(result)
        loading_message.destroy()

    Thread(target=wait_for_process).start()


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


def update_status(con_stat, bat_stat):
    status = (f"Connection status: {con_stat}\n"
              f"Battery condition: {bat_stat}\n")
    connection_status_text.config(state=tk.NORMAL)
    connection_status_text.delete(1.0, tk.END)
    connection_status_text.insert(tk.END, status)
    connection_status_text.config(state=tk.DISABLED)


def update_distance(total_distance_cm):
    status = (f"Total Distance: {total_distance_cm} cm \n")
    total_distance.config(state=tk.NORMAL)
    total_distance.delete(1.0, tk.END)
    total_distance.insert(tk.END, status)
    total_distance.config(state=tk.DISABLED)


def show_loading_message():
    loading_message = tk.Label(
        root, text="Please wait, processing...", font=("Arial", 16), fg="red")
    loading_message.pack(side=tk.TOP, pady=20)
    root.update_idletasks()
    return loading_message


def shutdown_trig():
    loading_message = show_loading_message()
    queue = Queue()
    p = Process(target=picommand.shutdown, args=(queue,))

    def wait_for_process():
        p.start()
        log_console("Shutdown...")
        p.join()
        result = queue.get()
        log_console(result)
        loading_message.destroy()

    Thread(target=wait_for_process).start()


def reboot_trig():
    loading_message = show_loading_message()
    queue = Queue()
    p = Process(target=picommand.reboot, args=(queue,))

    def wait_for_process():
        p.start()
        log_console("Rebooting...")
        p.join()
        result = queue.get()
        log_console(result)
        loading_message.destroy()

    Thread(target=wait_for_process).start()


def send_command_servo(command):
    global client_socket
    client_socket.send(command.encode('utf-8'))


def on_key_press(event):
    global keybind_stat
    if keybind_stat:
        key = event.keysym
        if key == 'Left':
            send_command_servo('LEFT')
            log_console("Left arrow")
        elif key == 'Right':
            send_command_servo('RIGHT')
            log_console("Right arrow")
        elif key == 'Up':
            send_command_servo('UP')
            log_console("Up arrow")
        elif key == 'Down':
            send_command_servo('DOWN')
            log_console("Down arrow")
        print(key)


def start_servo_server_trig():
    global client_socket, keybind_stat
    loading_message = show_loading_message()
    queue = Queue()
    p = Process(target=picommand.start_stream_servo, args=(queue,))

    def wait_for_process():
        p.start()
        log_console("Starting Servo Server...")
        p.join()
        result = queue.get()
        log_console(result)
        loading_message.destroy()
        connect_socket()

    def connect_socket():
        try:
            log_console("Connect to raspberry")
            # Replace with your Raspberry Pi's IP address
            client_socket.connect(('192.168.200.2', 5000))
            keybind_stat = True
            loading_message.destroy()
            log_console("Connected to Raspberry Pi")
        except Exception as e:
            loading_message.destroy()
            log_console(f"Connection failed: {e}")

    Thread(target=wait_for_process).start()


def main():
    global root, label, total_distance, console_text, sp_motor, radio_var, camera_left_right_scale, camera_up_down_scale, con_status, connection_status_text

    root = tk.Tk()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}")
    root.title("Robot Pipeline Inspection V1")

    frame_width, frame_height = 640, 480
    default_image = Image.new(
        'RGBA', (frame_width, frame_height), (255, 255, 255, 255))
    default_photo_image = ImageTk.PhotoImage(default_image)

    video_section = tk.Frame(
        root, highlightbackground="green", highlightthickness=2)
    video_section.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    status_title = tk.Label(video_section, text="Robot Status",
                            highlightbackground="blue", highlightthickness=2)
    status_title.pack(side=tk.TOP)

    default_text = (
        "Connection status : unchecked\n"
        "Battery condition : unchecked\n"
    )
    connection_status_text = tk.Text(video_section, height=3, width=52)
    connection_status_text.pack(side=tk.TOP)
    connection_status_text.insert(tk.END, default_text)
    connection_status_text.config(state=tk.DISABLED)

    btn_status_frame = tk.Frame(
        video_section, highlightbackground="green", highlightthickness=2)
    btn_status_frame.pack(side=tk.TOP)

    btn_check_con = tk.Button(
        btn_status_frame, text="Check Connection", command=check_status)
    btn_check_con.grid(column=0, row=0)

    btn_shutdown = tk.Button(
        btn_status_frame, text="Shutdown", command=shutdown_trig)
    btn_shutdown.grid(column=1, row=0)

    btn_reboot = tk.Button(
        btn_status_frame, text="Reboot", command=reboot_trig)
    btn_reboot.grid(column=2, row=0)

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

    btn_start_robot_stream = tk.Button(
        stream_section, text="Start Robot Stream", command=robot_start_stream_trig)
    btn_start_robot_stream.grid(column=3, row=0)

    btn_start_servo_stream = tk.Button(
        stream_section, text="Start Servo Stream", command=start_servo_server_trig)
    btn_start_servo_stream.grid(column=4, row=0)

    control_frame = tk.Frame(
        root, highlightbackground="red", highlightthickness=2)
    control_frame.pack(pady=20)

    control_frame.rowconfigure(2)
    control_frame.columnconfigure(2)

    total_distance = tk.Text(control_frame, height=2, width=30)
    total_distance.grid(row=0, column=0)
    total_distance.insert(tk.END, f"Total Distance : {Ttl_distance} cm")
    total_distance.config(state=tk.DISABLED)

    title_control = tk.Label(control_frame, text="Robot Control Configuration",
                             highlightbackground="blue", highlightthickness=2)
    title_control.grid(column=0, row=1, columnspan=3)

    motor_distance_frame = tk.Frame(
        control_frame, highlightbackground="blue", highlightthickness=7)
    motor_distance_frame.grid(column=0, row=2)

    title_distance = tk.Label(motor_distance_frame, text="Distance in cm",
                              highlightbackground="blue", highlightthickness=2)
    title_distance.grid(column=0, row=0)

    radio_var = tk.IntVar()
    radio_motor_type_A = tk.Radiobutton(
        motor_distance_frame, text="Default feet", variable=radio_var, value=1)
    radio_motor_type_A.grid(column=0, row=1)
    radio_motor_type_B = tk.Radiobutton(
        motor_distance_frame, text="Extended feet", variable=radio_var, value=2)
    radio_motor_type_B.grid(column=1, row=1)
    radio_motor_type_A.select()

    sp_motor = tk.Spinbox(motor_distance_frame, from_=-1000, to=1000)
    sp_motor.grid(column=1, row=2, rowspan=2)
    sp_motor.delete(0, tk.END)
    sp_motor.insert(0, "0")

    btn_run_motor = tk.Button(motor_distance_frame,
                              text="Run Motor", command=run_motor_trig)
    btn_run_motor.grid(column=2, row=1)

    servo_frame = tk.Frame(
        control_frame, highlightbackground="blue", highlightthickness=2)
    servo_frame.grid(column=2, row=2)
    servo_frame.bind("<KeyPress>", on_key_press)
    servo_frame.focus_set()

    camera_up_down_scale = tk.Scale(
        servo_frame, label="Degree", orient="vertical", from_=0, to=180)
    camera_up_down_scale.grid(column=1, row=2, rowspan=2)

    btn_camera_up = tk.Button(
        servo_frame, text="Camera Up/Down", command=run_motor_up_down)
    btn_camera_up.grid(column=2, row=2, rowspan=2, padx=20)

    camera_left_right_scale = tk.Scale(
        servo_frame, label="Degree", orient="horizontal", from_=0, to=180)
    camera_left_right_scale.grid(column=1, row=4, rowspan=2)

    btn_camera_left = tk.Button(
        servo_frame, text="Camera Left/Right", command=run_motor_left_right)
    btn_camera_left.grid(column=2, row=4, rowspan=2, padx=20)

    console_text = scrolledtext.ScrolledText(root, height=10)
    console_text.pack(fill="x", padx=10, pady=10)
    console_text.configure(state='disabled')

    root.mainloop()


if __name__ == '__main__':
    main()
