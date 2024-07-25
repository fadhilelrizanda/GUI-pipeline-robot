import asyncio
import platform
import subprocess


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


async def check_connection(ip_address, log_console):
    log_console(f"Checking connection to {ip_address}")
    result = await ping_connection(ip_address)
    if result:
        log_console(f"{ip_address} is reachable.")
    else:
        log_console(f"{ip_address} is not reachable.")

# Define a mock log_console function for demonstration


def log_console(message):
    print(message)


# Run the async main function
if __name__ == '__main__':
    ip_address = '192.168.1.1'  # Replace with your IP address
    asyncio.run(check_connection(ip_address, log_console))
