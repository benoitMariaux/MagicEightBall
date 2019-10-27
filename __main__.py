import sys
from datetime import datetime
from src.utils import init
from src.utils import remove
import src.utils.tools

def run(app_name):
    init.go_init(app_name)

def destroy(app_name):
    remove.go_remove(app_name)

if len(sys.argv) != 3:
    print('Need two arguments: app_name, [run or destroy]')
    sys.exit()

app_name = sys.argv[1]
action = sys.argv[2]

if (str(action) != 'run') and (str(action) != 'destroy'):
    print('The second argument must be "run" or "destroy"')
    sys.exit()

app_name = app_name + '-magic8ball-3b2c662647f18' # Avoid already used s3 name

globals()[action](app_name)
