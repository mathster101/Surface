import Surface
import os
import glob
import subprocess

PORT = 6969

while True:
    try:
        surfSlave = Surface.Surface_slave()
        surfSlave.startListener(PORT=PORT)
    except:
        for filename in glob.glob("./tmp_"):
            os.remove(filename)
        subprocess.run(f"sudo fuser -k -n tcp {PORT}")