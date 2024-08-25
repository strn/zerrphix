import sys


def unicode_argv():
    """Like sys.argv, but decodes all arguments."""
    args = []
    for arg in sys.argv:
        if isinstance(arg, bytes):
            arg = arg.decode(sys.getfilesystemencoding())
        args.append(arg)
    return args
