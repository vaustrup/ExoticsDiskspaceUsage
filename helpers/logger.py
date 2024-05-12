import sys

import logging
log = logging.getLogger("exoticsdiskspace")
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)4s]: %(message)s", "%d.%m.%Y %H:%M:%S")
handler.setFormatter(formatter)
log.addHandler(handler)
log.setLevel(logging.INFO)