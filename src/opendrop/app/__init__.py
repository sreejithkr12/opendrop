import sys

import gi

gi.require_version('Gtk', '3.0')

from opendrop.app.app import OpendropApplication


def main() -> None:
    app = OpendropApplication()

    app.run(sys.argv)

    print("Done.")


if __name__ == "__main__":
    main()
