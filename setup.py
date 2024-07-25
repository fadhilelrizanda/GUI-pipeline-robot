import cx_Freeze

executables = [cx_Freeze.Executable("main_script.py")]

cx_Freeze.setup(
    name="RobotPipeline",
    options={
        "build_exe": {
            "packages": ["paramiko", "picommand"],
            "include_files": [],
        }
    },
    executables=executables
)
