
import time
import subprocess
import src.prettyPrint as pretty

def getSwiftTagId(): #Add timeout to this function of ~60seconds ( lower priority) with countdown
    tagId = _getSwiftTagId()
    if not tagId:
        pretty.printWarning("Could not find Swift device")
        pretty.printPrompt("Please connect Swift device...")
    while not tagId:
        tagId = _getSwiftTagId()
        time.sleep(0.5)
    return tagId


def _getSwiftTagId():
    tagId = getProgrammedSwiftId()
    if tagId:
        return tagId
    tagId = getUnprogrammedSwiftId()
    if tagId:
        return tagId
    return False


def getProgrammedSwiftId():
    tagId = subprocess.check_output("sudo lsusb -v -d 0483:5740 | grep -i serial | awk 'NR==1{ print $3 }'", shell = True).strip()
    tagId = tagId.decode("utf-8").upper()
    if tagId:
        if "ERROR" in tagId:
            return False
        return tagId
    return False

def getUnprogrammedSwiftId():
    tagId = subprocess.check_output("sudo lsusb -v -d 0483:df11 | grep -i serial | awk '{ print $3 }'", shell = True).strip()
    tagId = tagId.decode("utf-8").lower()
    if tagId:
        if "error" in tagId:
            return False
        return tagId
    return False
