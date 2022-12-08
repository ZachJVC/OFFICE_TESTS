END      = '\33[0m'
BOLD     = '\33[1m'
ITALIC   = '\33[3m'
URL      = '\33[4m'
BLINK    = '\33[5m'
BLINK2   = '\33[6m'
SELECTED = '\33[7m'

BLACK  = '\33[30m'
RED    = '\33[31m'
GREEN  = '\33[32m'
YELLOW = '\33[33m'
BLUE   = '\33[34m'
VIOLET = '\33[35m'
BEIGE  = '\33[36m'
WHITE  = '\33[37m'

def formatError(message):
    return RED+message+END

def printError(message):
    print(formatError(message))

def formatPrompt(message):
    return YELLOW+BOLD+message+END

def printPrompt(message):
    print(formatPrompt(message))

def formatInfo(message):
    return BLUE+BOLD+message+END

def printInfo(message):
    print(formatInfo(message))

def formatWarning(message):
    return YELLOW+message+END

def printWarning(message):
    print(formatWarning(message))

def formatSuccess(message):
    return GREEN+BLINK+message+END

def printSuccess(message):
    print(formatSuccess(message))

def formatFailure(message):
    return RED+BLINK+message+END

def printFailure(message):
    print(formatFailure(message))

def formatComplete(message):
    return WHITE+BOLD+message+END

def printComplete(message):
    print(formatComplete(message))
