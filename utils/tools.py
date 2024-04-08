import os
import sys
import subprocess
import traceback


class PIP(object):
    """A class to interact with PIP from within the python script."""

    @classmethod
    def works(cls):
        """Check if pip is valid"""  # regardless of whether pip is valid, you definitely are
        try:
            import pip
            return True
        except ImportError:
            return False

    @classmethod
    def run(cls, command, check_output=False):
        """Run pip command"""
        if not cls.works():
            raise RuntimeError("Could Not Import PIP.")

        try:
            return PIP.run_python_m(*command.split(), check_output=check_output)
        except subprocess.CalledProcessError as e:
            return e.returncode
        except:
            traceback.print_exc()
            print("Error running PIP with '-m' method.")

    @classmethod
    def run_python_m(cls, *args, **kwargs):
        """Run pip via Python -m"""
        check_output = kwargs.pop('check_output', False)
        check = subprocess.check_output if check_output else subprocess.check_call

        return check([sys.executable, '-m', 'pip'] + list(args))

    @classmethod
    def run_install(cls, cmd, quiet=False, check_output=False):
        """Install valid pip module or query"""
        return cls.run("install %s%s" % ('-q ' if quiet else '', cmd), check_output)

    @classmethod
    def install_requirements(cls):
        """Install Bot Requirements"""
        return cls.run_install('--upgrade -r requirements.txt')


def press_continue():
    """Cross-Platform function to wait for (any) keypress"""
    result = None
    if os.name == 'nt':
        import msvcrt
        result = msvcrt.getch()
    else:
        import termios
        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        try:
            result = sys.stdin.read(1)
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

    return result

def get_env(variable):
    """Get Environment Variable"""
    return os.getenv(variable)

def get_env_bool(variable):
    """Get Environment Variable as Boolean"""
    return str(get_env(variable)).lower() in ['true', '1', 'yes', 'y']