import paramiko


class Picommand:
    def __init__(self, hostname, port, username, password, raspberry_ip):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.raspberry_ip = raspberry_ip

    def ssh_command(self, command):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"{self.port} {self.username} {self.password} {self.raspberry_ip} ")

        try:
            client.connect(self.hostname, port=self.port,
                           username=self.username, password=self.password)
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()

            if error:
                return output, error
            return output, None

        except Exception as e:
            return "", str(e)

        finally:
            client.close()

    def reboot(self, queue):
        command = "sudo reboot"
        output, error = self.ssh_command(command)

        if error:
            result = f"Reboot failed: {error}"
        else:
            result = "Reboot successful"

        queue.put(result)

    def shutdown(self, queue):
        command = "sudo shutdown -h 0"
        output, error = self.ssh_command(command)
        if error:
            result = f"Shutdown failed: {error}"
        else:
            result = "Shutdown successful"

        queue.put(result)

    def check_connection(self):
        try:
            # Create an SSH client
            ssh = paramiko.SSHClient()

            # Automatically add the server's host key (this is insecure)
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the server
            ssh.connect(hostname=self.hostname, port=self.port,
                        username=self.username, password=self.password)

            # Close the connection
            ssh.close()

            return True
        except Exception as e:
            print(f"Error while connecting: {e}")
            return False

    def check_voltage(self):
        command = "vcgencmd get_throttled"
        output, error = self.ssh_command(command)
        if error:
            output = "Not Connected"
            return output
        return output

    def motor_run_command(self, distance, motor_type, queue):
        if distance < 0:
            direction = 0
        else:
            direction = 1
        if motor_type == 1:
            time = float(distance/27.5)
        else:
            time = float(distance/9)
        command = f"python /home/robot/code/raspberry-pipe-code/motor.py --time {abs(time)} --d {direction}"
        output, error = self.ssh_command(command)
        if error:
            output = f"Error : {error}"
        queue.put(output)

    def run_servo_command(angle, servo):
        command = f"python /home/robot/code/raspberry-pipe-code/motor_servo.py --d {angle} --s {servo}"
        return command

    def reset_servo(self, queue):
        command1 = f"python /home/robot/code/raspberry-pipe-code/motor_servo.py --d {90} --s {1}"
        output, error = self.ssh_command(command1)
        command2 = f"python /home/robot/code/raspberry-pipe-code/motor_servo.py --d {90} --s {1}"
        output, error = self.ssh_command(command2)
        return output

    def start_stream(self, queue):
        command = f"python /home/robot/code/raspberry-pipe-code/stream.py"
        output, error = self.ssh_command(command)
        if error:
            output = f"Error : {error}"
        queue.put(output)

    def start_stream_servo(self, queue):
        command = f"python /home/robot/code/raspberry-pipe-code/servo_server.py"
        output, error = self.ssh_command(command)
        if error:
            output = f"Error : {error}"
        queue.put(output)

    def start_stream_motor(self, queue):
        command = f"python /home/robot/code/raspberry-pipe-code/motor_server.py"
        output, error = self.ssh_command(command)
        if error:
            result = f"Error : {error}"
        else:
            result = "Motor Stream Started"
        queue.put(result)

    def kill_active_port(self, queue, port_num):
        command = f"kill -9 $(lsof -t -i tcp:{port_num})"
        output, error = self.ssh_command(command)
        if error:
            output = f"Error : {error}"
        queue.put(output)
