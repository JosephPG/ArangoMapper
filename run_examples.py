import subprocess
import sys

from loguru import logger

logger.remove()
logger.add(sys.stdout, format="<blue><b>{message}</b></blue>")


def run_module(module_name):
    try:
        subprocess.run([sys.executable, "-m", f"example.{module_name}"], check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)


def main():
    modules = ["write", "read_1_basic", "read_2_raw", "read_3_advanced", "transaction"]

    for module in modules:
        logger.info(f"\n----------------- Running: example.{module} -----------------")
        run_module(module)
        logger.info("--------------------- End example.{module} ---------------------")


if __name__ == "__main__":
    main()
