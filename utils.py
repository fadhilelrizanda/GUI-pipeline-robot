from threading import Thread
from multiprocessing import Process, Queue
import command
from dotenv import load_dotenv
import os
from PIL import Image, ImageTk
import tkinter as tk
import struct
import io
import socket
import time
import cv2
import numpy as np
# Load environment
load_dotenv()

host_name = os.getenv('ROBOT_HOSTNAME')
port = int(os.getenv("PORT"))
username = os.getenv("USERNAME_ROBOT")
password = os.getenv("PASSWORD_ROBOT")
raspberry_ip = os.getenv("RASPI_IP")

picommand = command.Picommand(
    host_name, port, username, password, raspberry_ip)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Define Variable
stream_status = False
recording_status = False  # Added variable to track recording status
current_distance = 0


def change_current_distance(val):
    global current_distance
    current_distance = val


def check_status(log_console, show_loading_message, update_status, connection_status_text):
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


def reboot_trig(show_loading_message, log_console):
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


def shutdown_trig(show_loading_message, log_console):
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


def start_stream(log_console, tk_image, record=True):
    global stream_status, recording_status
    stream_status = True
    recording_status = record  # Set recording status based on the parameter

    if stream_status:
        Thread(target=update_video_image, args=(log_console, tk_image)).start()


def stop_stream():
    global stream_status, recording_status
    stream_status = False
    recording_status = False  # Stop recording when streaming stops


def update_video_image(log_console, label):
    global raspberry_ip, recording_status
    raspi_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        log_console(f"Try to connect to raspberry pi ip {raspberry_ip}")
        raspi_socket.connect((raspberry_ip, 8080))
        connection = raspi_socket.makefile('rb')
    except Exception as e:
        log_console(f"Error : \n  {e}")
        return  # Exit the function if the connection fails

    if recording_status:
        first_frame_time = None
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = None  # Initialize the video writer as None

    global stream_status, current_distance
    while stream_status:
        try:
            image_len = struct.unpack(
                '<L', connection.read(struct.calcsize('<L')))[0]
            if not image_len:
                continue

            image_data = connection.read(image_len)
            image = Image.open(io.BytesIO(image_data))

            # Convert PIL image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Add current time overlay
            # current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            cv2.putText(cv_image, f"Jarak : {current_distance}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 87, 51), 2, cv2.LINE_AA)

            # Convert back to PIL Image to display in Tkinter
            image_with_time = Image.fromarray(
                cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
            tk_image = ImageTk.PhotoImage(image_with_time)
            label.config(image=tk_image)
            label.image = tk_image

            if recording_status:
                current_time = time.time()

                if first_frame_time is None:
                    first_frame_time = current_time
                    frame_interval = 1.0 / 10.0  # Default to 20 FPS
                else:
                    frame_interval = current_time - first_frame_time
                    first_frame_time = current_time

                fps = 1.0 / frame_interval

                if out is None:
                    width, height = image.size
                    out = cv2.VideoWriter(
                        'stream_record.avi', fourcc, fps, (width, height)
                    )

                out.write(cv_image)  # Write frame to video file

        except Exception as e:
            log_console(f"Error : \n  {e}")
            break

        time.sleep(0.05)

    if recording_status:
        out.release()  # Release the video file when streaming stops


def robot_start_stream_trig(show_loading_message, log_console, change_server_stat):
    loading_message = show_loading_message()
    queue = Queue()
    p = Process(target=picommand.start_stream, args=(queue,))

    def wait_for_process():
        p.start()
        log_console(f"Camera Stream Started...")
        loading_message.destroy()
        change_server_stat(0, True)
        p.join()
        result = queue.get()
        log_console(result)
    Thread(target=wait_for_process).start()


def start_servo_server_trig(show_loading_message, log_console, change_server_stat):
    global client_socket, keybind_stat
    loading_message = show_loading_message()
    queue = Queue()
    p = Process(target=picommand.start_stream_servo, args=(queue,))

    def wait_for_process():
        p.start()
        log_console("Servo Server Started...")
        loading_message.destroy()
        change_server_stat(1, True)
        p.join()
        result = queue.get()
        log_console(result)

    Thread(target=wait_for_process).start()


def start_motor_server_trig(show_loading_message, log_console, change_server_stat):
    global client_socket, keybind_stat
    loading_message = show_loading_message()
    queue = Queue()
    p = Process(target=picommand.start_stream_motor, args=(queue,))

    def wait_for_process():
        p.start()
        log_console("Motor Server Started...")
        loading_message.destroy()
        change_server_stat(2, True)
        p.join()
        result = queue.get()
        log_console(result)

    Thread(target=wait_for_process).start()


def run_motor_trig():
    global Ttl_distance, total_distance
    loading_message = show_loading_message()
    check_val = int(sp_motor.get())
    check_motor_type = radio_var.get()
    Ttl_distance += check_val
    utils.update_distance(total_distance, Ttl_distance)
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


def run_motor_up_down(camera_up_down_scale, log_console):
    degree_servo = camera_up_down_scale.get()
    servo_code = 2
    if degree_servo < 0:
        log_console(f"Run servo down {degree_servo} code {servo_code}")
    else:
        log_console(f"Run servo up {degree_servo} code {servo_code}")
    angle = abs(degree_servo)
    p = Process(target=run_servo_command, args=(angle, servo_code))
    p.start()


def reset_servo_trig(log_console):
    queue = Queue()
    p = Process(target=picommand.reset_servo, args=(queue,))
    p.start()
    log_console("Reset Servo")


def kill_server(server_code, show_loading_message, log_console, change_server_stat):
    if server_code == 0:
        port_num = 8080
    elif server_code == 1:
        port_num = 5000
    elif server_code == 2:
        port_num = 5050
    else:
        log_console("Wrong server code")
    change_server_stat(server_code, False)
    loading_message = show_loading_message()
    queue = Queue()
    p = Process(target=picommand.kill_active_port, args=(queue, port_num))

    def wait_for_process():
        p.start()
        log_console(f"Kill server... {port_num}")
        p.join()
        result = queue.get()
        log_console(result)
        loading_message.destroy()

    Thread(target=wait_for_process).start()


def update_distance(total_distance, total_distance_cm):
    status = (f"Total Distance: {total_distance_cm} cm \n")
    total_distance.config(state=tk.NORMAL)
    total_distance.delete(1.0, tk.END)
    total_distance.insert(tk.END, status)
    total_distance.config(state=tk.DISABLED)


def send_command_servo(command):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # replace 'raspberry_pi_ip' with the actual IP address
    client_socket.connect(('192.168.200.2', 5000))
    client_socket.send(command.encode('utf-8'))


def send_command_motor_server(command):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # replace 'raspberry_pi_ip' with the actual IP address
    client_socket.connect(('192.168.200.2', 5050))
    client_socket.send(command.encode('utf-8'))
    client_socket.close()


def on_key_press(event, keybind_stat, keybind_motor, log_console):
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
    if keybind_motor:
        key = event.keysym
        if key == 'w':
            send_command_motor_server('FORWARD')
            log_console("FORWARD")
        elif key == 's':
            send_command_motor_server('BACKWARD')
            log_console("BACKWARD")
        elif key == 'a':
            send_command_motor_server('A')
            log_console("LEFT")
        elif key == 'd':
            send_command_motor_server('D')
            log_console("RIGHT")

        print(key)
