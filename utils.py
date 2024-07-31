from threading import Thread
from multiprocessing import Process, Queue
import command
from dotenv import load_dotenv
import os
import tkinter as tk

# Load environment
load_dotenv()

host_name = os.getenv('HOSTNAME_ROBOT')
port = int(os.getenv("PORT"))
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
raspberry_ip = os.getenv("RASPI_IP")

picommand = command.Picommand(
    host_name, port, username, password, raspberry_ip)

def on_key_press(event,keybind_stat,send_command_servo,log_console):
    if keybind_stat:
        key = event.keysym
        if key == 'Left':
            # send_command_servo('LEFT')
            log_console("Left arrow")
        elif key == 'Right':
            # send_command_servo('RIGHT')
            log_console("Right arrow")
        elif key == 'Up':
            # send_command_servo('UP')
            log_console("Up arrow")
        elif key == 'Down':
            # send_command_servo('DOWN')
            log_console("Down arrow")
        print(key)


def set_focus_frame_trig(frame):
        frame.focus_set()

def reboot_trig(show_loading_message,log_console):
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

def shutdown_trig(show_loading_message,log_console):
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

def update_status(connection_status_text,con_stat, bat_stat):
    status = (f"Connection status: {con_stat}\n"
              f"Battery condition: {bat_stat}\n")
    connection_status_text.config(state=tk.NORMAL)
    connection_status_text.delete(1.0, tk.END)
    connection_status_text.insert(tk.END, status)
    connection_status_text.config(state=tk.DISABLED)


def update_distance(total_distance,total_distance_cm):
    status = (f"Total Distance: {total_distance_cm} cm \n")
    total_distance.config(state=tk.NORMAL)
    total_distance.delete(1.0, tk.END)
    total_distance.insert(tk.END, status)
    total_distance.config(state=tk.DISABLED)