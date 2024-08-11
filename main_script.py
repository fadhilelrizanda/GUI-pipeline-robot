# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageTk
import os
from dotenv import load_dotenv
from threading import Thread
import command
import io
import threading
from multiprocessing import Process, Queue
import time
import utils
import multiprocessing
import numpy as np
# Load environment
load_dotenv()

host_name = os.getenv('ROBOT_HOSTNAME')
port = int(os.getenv("PORT"))
username = os.getenv("USERNAME_ROBOT")
password = os.getenv("PASSWORD_ROBOT")
raspberry_ip = os.getenv("RASPI_IP")

# Define Variable
camera_server = False
servo_server = False
motor_server = False

stream_status = False
con_status = "unchecked"
keybind_stat = True
motor_keybind = True

picommand = command.Picommand(
    host_name, port, username, password, raspberry_ip)

Ttl_distance = 0

# GUI Custumize
space_1 = 5
main_font = "Verdana"
color1 = "#6482AD"
color2 = "#7FA1C3"
color3 = "#E2DAD6"
color4 = "#F5EDED"
r_color = "#FF0000"


def change_server_stat(stat, val):
    print(f"change server stat {stat} {val}")
    global camera_server, servo_server, motor_server
    if stat == 0:
        camera_server = val
    elif stat == 1:
        servo_server = val
    elif stat == 2:
        motor_server = val
    else:
        log_console("Wrong value ")


def show_loading_message():
    loading_message = tk.Label(
        root, text="Please wait, processing...", font=("Arial", 16), fg="red")
    loading_message.pack(side=tk.TOP, pady=20)
    root.update_idletasks()
    return loading_message


def log_console(message):
    console_text.configure(state='normal')
    console_text.insert(tk.END, message + '\n')
    console_text.configure(state='disabled')
    console_text.yview(tk.END)


def update_status(con_stat, bat_stat):
    global connection_status_text
    status = (f"Connection status: {con_stat}\n"
              f"Battery condition: {bat_stat}\n")
    connection_status_text.config(state=tk.NORMAL)
    connection_status_text.delete(1.0, tk.END)
    connection_status_text.insert(tk.END, status)
    connection_status_text.config(state=tk.DISABLED)


def update_status_server():
    global server_status, camera_server, servo_server, motor_server, root
    status = (f"Camera Server : {camera_server} \n"
              f"Servo Server : {servo_server} \n"
              f"Motor Server : {motor_server}")
    server_status.config(state=tk.NORMAL)
    server_status.delete(1.0, tk.END)
    server_status.insert(tk.END, status)
    server_status.config(state=tk.DISABLED)
    root.after(5000, update_status_server)


def set_focus_frame_trig(frame):
    frame.focus_set()


def on_focus_in(event):
    event.widget.config(background="blue")


def on_focus_out(event):
    event.widget.config(background="red")


def remove_focus_frame_trig(root):
    root.focus_set()


def main():
    global root, space_1, camera_server, servo_server, motor_server, connection_status_text, server_status, label, total_distance, console_text, sp_motor, radio_var, camera_left_right_scale, camera_up_down_scale, con_status, connection_status_text

    root = tk.Tk()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}")
    root.title("Robot Pipeline Inspection V1")
    root.configure(bg=color1)

    frame_width, frame_height = 640, 480
    default_image = Image.new(
        'RGBA', (frame_width, frame_height), (255, 255, 255, 255))
    default_photo_image = ImageTk.PhotoImage(default_image)

    video_section = tk.Frame(
        root, bg=color1)
    video_section.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

    # Status Section
    status_title = tk.Label(
        video_section, text="Robot Status", bg=color4, padx=space_1+30, pady=space_1, font=("Verdana", 16))
    status_title.pack(side=tk.TOP, pady=5)

    default_text = (
        "Connection status  : unchecked\n"
        "Battery condition   : unchecked\n"
    )
    connection_status_text = tk.Text(
        video_section, height=2, width=52, bg=color4)
    connection_status_text.pack(side=tk.TOP, pady=10)
    connection_status_text.insert(tk.END, default_text)
    connection_status_text.config(state=tk.DISABLED, font=(main_font, 10))

    btn_status_frame = tk.Frame(
        video_section, bg=color1)
    btn_status_frame.pack(side=tk.TOP, padx=20)

    btn_check_con = tk.Button(
        btn_status_frame, text="Check Connection",  command=lambda: utils.check_status(log_console, show_loading_message, update_status, connection_status_text), font=(main_font, 10), padx=5, pady=5, fg=color4, bg="#399918", borderwidth=1, highlightthickness=0)
    btn_check_con.grid(column=0, row=0, padx=20)

    btn_shutdown = tk.Button(
        btn_status_frame, font=(main_font, 10), text="Shutdown", command=lambda: utils.shutdown_trig(show_loading_message, log_console), bg=r_color, padx=5, pady=5, fg="#FFE8C5", borderwidth=1, highlightthickness=0)
    btn_shutdown.grid(column=1, row=0, padx=20)

    btn_reboot = tk.Button(
        btn_status_frame, font=(main_font, 10), text="Reboot", command=lambda: utils.reboot_trig(show_loading_message, log_console), bg="#FF8F00", padx=5, pady=5, fg="#FFE8C5", borderwidth=1, highlightthickness=0)
    btn_reboot.grid(column=2, row=0, padx=20)

    # Video Section
    label = tk.Label(video_section, image=default_photo_image)
    label.pack(side=tk.TOP, pady=10)

    stream_section = tk.Frame(
        video_section, bg=color1)
    stream_section.pack()

    # Button Stream Section
    btn_start_stream = tk.Button(
        stream_section, text="Start Stream", command=lambda: utils.start_stream(log_console, label), font=(main_font, 10), bg="#399918", padx=5, pady=5, fg=color4, borderwidth=1, highlightthickness=0)
    btn_start_stream.grid(column=0, row=0, padx=10)

    btn_stop_stream = tk.Button(
        stream_section, text="Stop Stream", command=utils.stop_stream, bg=r_color, padx=5, pady=5, fg="#FFE8C5", borderwidth=1, highlightthickness=0, font=(main_font, 10))
    btn_stop_stream.grid(column=1, row=0, padx=10)

    # Control Section
    control_frame = tk.Frame(
        root, bg=color1)
    control_frame.pack(pady=20)

    control_frame.rowconfigure(3)
    control_frame.columnconfigure(2)

    title_control = tk.Label(control_frame, text="Robot Control Configuration",
                             font=(main_font, 12), padx=5, pady=5)
    title_control.grid(column=0, row=0, columnspan=3)

    server_status = tk.Text(control_frame, height=3,
                            width=30, font=(main_font, 10))
    server_status.insert(
        tk.END, f"Camera Server : {camera_server} \nServo Server : {servo_server} \nMotor Server : {motor_server}")
    server_status.config(state=tk.DISABLED)
    server_status.grid(row=1, column=1, pady=5)

    total_distance = tk.Text(control_frame, height=2,
                             width=30, font=(main_font, 10))
    total_distance.grid(row=1, column=0)
    total_distance.insert(tk.END, f"Total Distance : {Ttl_distance} cm")
    total_distance.config(state=tk.DISABLED)

    frame_start_server = tk.Frame(
        control_frame, bg=color1)
    frame_start_server.grid(column=0, row=2, pady=10, columnspan=3)

    btn_start_stream_camera = tk.Button(frame_start_server,
                                        text="Start Server Camera", command=lambda: utils.robot_start_stream_trig(show_loading_message, log_console, change_server_stat), font=(main_font, 10), padx=5, pady=5, fg=color4, bg="#399918", borderwidth=1, highlightthickness=0)
    btn_start_stream_camera.grid(column=0, row=0, padx=5, pady=5)

    btn_start_stream_servo = tk.Button(frame_start_server,
                                       text="Start Server Servo", command=lambda: utils.start_servo_server_trig(show_loading_message, log_console, change_server_stat), font=(main_font, 10), padx=5, pady=5, fg=color4, bg="#399918", borderwidth=1, highlightthickness=0)
    btn_start_stream_servo.grid(column=1, row=0, padx=5, pady=5)

    btn_start_stream_motor = tk.Button(frame_start_server,
                                       text="Start Server Motor", command=lambda: utils.start_motor_server_trig(show_loading_message, log_console, change_server_stat), font=(main_font, 10), padx=5, pady=5, fg=color4, bg="#399918", borderwidth=1, highlightthickness=0)
    btn_start_stream_motor.grid(column=2, row=0, padx=5, pady=5)

    frame_kill_server = tk.Frame(
        control_frame, bg=color1)
    frame_kill_server.grid(column=0, row=3, columnspan=3)

    btn_kill_camera = tk.Button(frame_kill_server,
                                text="Kill Server Camera", command=lambda: utils.kill_server(0, show_loading_message, log_console, change_server_stat), bg=r_color, padx=5, pady=5, fg="#FFE8C5", borderwidth=1, highlightthickness=0, font=(main_font, 10))
    btn_kill_camera.grid(column=0, row=0, padx=5)

    btn_kill_servo = tk.Button(frame_kill_server,
                               text="Kill Server Servo", command=lambda: utils.kill_server(1, show_loading_message, log_console, change_server_stat), bg=r_color, padx=5, pady=5, fg="#FFE8C5", borderwidth=1, highlightthickness=0, font=(main_font, 10))
    btn_kill_servo.grid(column=1, row=0, padx=5)

    btn_kill_motor = tk.Button(frame_kill_server,
                               text="Kill Server Motor",  command=lambda: utils.kill_server(2, show_loading_message, log_console, change_server_stat), bg=r_color, padx=5, pady=5, fg="#FFE8C5", borderwidth=1, highlightthickness=0, font=(main_font, 10))
    btn_kill_motor.grid(column=2, row=0, padx=5)

    # Center the buttons in the frame
    frame_kill_server.grid_columnconfigure(0, weight=1)
    frame_kill_server.grid_columnconfigure(1, weight=1)
    frame_kill_server.grid_columnconfigure(2, weight=1)

    # Distance Section
    motor_distance_frame = tk.Frame(
        control_frame, highlightbackground="blue", highlightthickness=7)
    motor_distance_frame.grid(column=0, row=4, pady=10)

    title_distance = tk.Label(motor_distance_frame, text="Distance in cm",
                              highlightbackground="blue", highlightthickness=2)
    title_distance.grid(column=0, row=0)

    # radio_var = tk.IntVar()
    # radio_motor_type_A = tk.Radiobutton(
    #     motor_distance_frame, text="Default feet", variable=radio_var, value=1)
    # radio_motor_type_A.grid(column=0, row=1)
    # radio_motor_type_B = tk.Radiobutton(
    #     motor_distance_frame, text="Extended feet", variable=radio_var, value=2)
    # radio_motor_type_B.grid(column=1, row=1)
    # radio_motor_type_A.select()

    sp_motor = tk.Spinbox(motor_distance_frame, from_=-1000, to=1000)
    sp_motor.grid(column=1, row=2, rowspan=2)
    sp_motor.delete(0, tk.END)
    sp_motor.insert(0, "0")

    btn_run_motor = tk.Button(motor_distance_frame,
                              text="Run Motor", command=lambda: utils.change_current_distance(sp_motor.get()))
    btn_run_motor.grid(column=2, row=1)

    # Keybind Control
    keybind_frame = tk.Frame(
        control_frame, highlightbackground="red", highlightthickness=5, width=200, height=100)
    keybind_frame.grid(column=1, row=4)
    keybind_frame.bind("<FocusIn>", on_focus_in)
    keybind_frame.bind("<FocusOut>", on_focus_out)
    keybind_frame.bind("<KeyPress>", lambda event: utils.on_key_press(
        event, keybind_stat, motor_keybind, log_console))

    btn_set_focus = tk.Button(keybind_frame, text="Activate Keybind",
                              command=lambda: set_focus_frame_trig(keybind_frame))
    btn_set_focus.grid(column=0, row=0, padx=10, pady=10)

    btn_set_unfocus = tk.Button(keybind_frame, text="Disable Keybind",
                                command=lambda: remove_focus_frame_trig(root))
    btn_set_unfocus.grid(column=1, row=0)

    # Camera Up down Section
    servo_frame = tk.Frame(
        control_frame, highlightbackground="blue", highlightthickness=2)
    servo_frame.grid(column=0, row=5)
    camera_up_down_scale = tk.Scale(
        servo_frame, label="Degree", orient="vertical", from_=0, to=180)
    camera_up_down_scale.grid(column=1, row=2, rowspan=2)

    btn_camera_up = tk.Button(
        servo_frame, text="Camera Up/Down", command=lambda: utils.run_motor_up_down(camera_up_down_scale, log_console))
    btn_camera_up.grid(column=2, row=2, rowspan=2, padx=20)

    camera_left_right_scale = tk.Scale(
        servo_frame, label="Degree", orient="horizontal", from_=0, to=180)
    camera_left_right_scale.grid(column=1, row=4, rowspan=2)

    btn_camera_left = tk.Button(
        servo_frame, text="Camera Left/Right", command=utils.run_motor_left_right)
    btn_camera_left.grid(column=2, row=4, rowspan=2, padx=20)

    btn_reset_servo = tk.Button(
        servo_frame, text="Reset Servo", command=lambda: utils.reset_servo_trig(log_console))
    btn_reset_servo.grid(column=3, row=4, rowspan=2, padx=20)

    # Console Section
    console_text = scrolledtext.ScrolledText(root, height=10)
    console_text.pack(fill="x", padx=10, pady=10)
    console_text.configure(state='disabled')
    update_status_server()
    root.mainloop()


if __name__ == '__main__':

    multiprocessing.set_start_method('spawn')  # Add this line
    multiprocessing.freeze_support()
    main()
