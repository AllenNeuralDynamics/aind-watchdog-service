"""Build watchdog service executable"""

from PyInstaller import __main__ as pyi


def main():
    """Build watchdog service executable using PyInstaller
    """
    args = [
        "src/aind_watchdog_service/main.py",
        "--name",
        "aind-watchdog-service",
        "-i",
        "src/aind_watchdog_service/icon/watchdog.ico",
        "--additional-hooks-dir=.",
        "--noconsole",
        "--onefile",
        "--clean"
    ]
    pyi.run(args)


if __name__ == "__main__":
    main()
