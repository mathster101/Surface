import Surface
import os
import glob
import subprocess

PORT = 6969

while True:
    try:
        surfSlave = Surface.Surface_slave()
        surfSlave.startListener()
    except Exception as e:
        print(f"ERROR:{e}")
        for filename in glob.glob("./tmp_"):
            os.remove(filename)
        subprocess.run(f"sudo fuser -k -n tcp {PORT}", shell = True)
        surfSlave = None