import pathlib

BASE_PATH = pathlib.Path(__file__).parent.parent
COLORS_PATH = BASE_PATH / "colors"
COORDINATES_PATH = BASE_PATH / "coordinates"

MIGRATIONS_PATH = pathlib.Path(__file__).parent / "migrate"

from migrations.migration import *
from migrations.helpers import *
from migrations.exceptions import *
