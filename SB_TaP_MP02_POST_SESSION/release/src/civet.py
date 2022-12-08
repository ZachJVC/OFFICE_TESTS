import time
import subprocess
import src.prettyPrint as pretty

def getProgrammedCivetId():
    tagId = subprocess.check_output("sudo lsusb -v -d 1915:520d | grep -i serial | awk 'NR==1{ print $3 }'", shell = True).strip()
    tagId = tagId.decode("utf-8").lower()
    if tagId:
        if "error" in tagId:
            return False
        return tagId
    return False