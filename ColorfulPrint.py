def print_red(msg, **kwargs):
    print(f"\033[31m{msg}\033[0m", end='', **kwargs)

def print_green(msg, **kwargs):
    print(f"\033[32m{msg}\033[0m", end='', **kwargs)

def print_yellow(msg, **kwargs):
    print(f"\033[33m{msg}\033[0m", end='', **kwargs)

def print_blue(msg, **kwargs):
    print(f"\033[34m{msg}\033[0m", end='', **kwargs)

