_COMMANDS = {}


def register_command(function):
    _COMMANDS[function.__name__] = function


def execute_command(command, *args):
    try:
        try:
            _COMMANDS[command](*args)
        except TypeError:
            print("Invalid arguments.")
            return False
    except KeyError:
        if command == 'help':
            _command_help()
        else:
            return False

    return True


def _command_help():
    print("\nCOMMAND HELP\n")
    for command in _COMMANDS:
        print(_COMMANDS[command].__name__)
        print("-----------------------------")
        if _COMMANDS[command].__doc__:
            print(_COMMANDS[command].__doc__)
        print()