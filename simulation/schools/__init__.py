from common import *

for modname in glob("schools/*.py"):
    filename = modname.split( os.path.sep )[1]
    if not filename.startswith("__"):
        school = filename.split(".")[0]
        mod = __import__("schools."+school, fromlist=[school])
        globals()[school] = getattr(mod, school)
