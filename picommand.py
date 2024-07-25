import paramiko


def ssh_command(hostname, port, username, password, command):
    # Create an SSH client
    client = paramiko.SSHClient()

    # Automatically add the server's SSH key (use with caution)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Connect to the server
        client.connect(hostname, port=port,
                       username=username, password=password)

        # Execute the command
        stdin, stdout, stderr = client.exec_command(command)

        # Read the output
        output = stdout.read().decode()
        error = stderr.read().decode()

        # Print the output and error (if any)
        print("Output:\n", output)
        res = output
        if error:
            print("Error:\n", error)
            res = error
            # log_console(res)
        return res

    except Exception as e:
        print(f"An error occurred: {e}")
        res = e
        # log_console(res)
    finally:
        # Close the connection
        client.close()


def motor_run_command(time, direction):
    command = f"python /home/robot/code/raspberry-pipe-code/motor.py --time {abs(time)} --d {direction}"
    return command


def run_servo_command(angle, servo):
    command = f"python /home/robot/code/raspberry-pipe-code/motor_servo.py --d {angle} --s {servo}"
    return command


def start_stream():
    command = f"python /home/robot/code/raspberry-pipe-code/stream.py "
    return command


def reboot():
    command = f"sudo reboot"
    return command


def shutdown():
    command = f"sudo shutdown -h 0"
    return command
