"""Rebuild the gravship plan: python3 build.py  ->  grav.json + gravship-plan.html"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
r = subprocess.run([sys.executable, os.path.join(HERE, "grav.py"), os.path.join(HERE, "grav.json")], cwd=HERE)
if r.returncode:
    sys.exit("grav.py reported errors (see above); page not rebuilt")
page = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
data = open(os.path.join(HERE, "grav.json"), encoding="utf-8").read()
assert page.count("__DATA__") == 1
open(os.path.join(HERE, "gravship-plan.html"), "w", encoding="utf-8").write(page.replace("__DATA__", data))
print("wrote gravship-plan.html")
