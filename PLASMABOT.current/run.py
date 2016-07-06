from __future__ import print_function

import os
import gc
import sys
import time
import traceback
import subprocess


class GIT(object):
    @classmethod
    def works(cls):
        try:
            return bool(subprocess.check_output('git --version', shell=True))
        except:
            return False


class PIP(object):
    @classmethod
    def run(cls, command, check_output=False):
        if not cls.works():
            raise RuntimeError("Could not import pip.")

        try:
            return PIP.run_python_m(*command.split(), check_output=check_output)
        except subprocess.CalledProcessError as e:
            return e.returncode
        except:
            traceback.print_exc()
            print("Error using -m method")

    @classmethod
    def run_python_m(cls, *args, **kwargs):
        check_output = kwargs.pop('check_output', False)
        check = subprocess.check_output if check_output else subprocess.check_call
        return check([sys.executable, '-m', 'pip'] + list(args))

    @classmethod
    def run_pip_main(cls, *args, **kwargs):
        import pip

        args = list(args)
        check_output = kwargs.pop('check_output', False)

        if check_output:
            from io import StringIO

            out = StringIO()
            sys.stdout = out

            try:
                pip.main(args)
            except:
                traceback.print_exc()
            finally:
                sys.stdout = sys.__stdout__

                out.seek(0)
                pipdata = out.read()
                out.close()

                print(pipdata)
                return pipdata
        else:
            return pip.main(args)

    @classmethod
    def run_install(cls, cmd, quiet=False, check_output=False):
        return cls.run("install %s%s" % ('-q ' if quiet else '', cmd), check_output)

    @classmethod
    def run_show(cls, cmd, check_output=False):
        return cls.run("show %s" % cmd, check_output)

    @classmethod
    def works(cls):
        try:
            import pip
            return True
        except ImportError:
            return False

    @classmethod
    def get_module_version(cls, mod):
        try:
            out = cls.run_show(mod, check_output=True)

            if isinstance(out, bytes):
                out = out.decode()

            datas = out.replace('\r\n', '\n').split('\n')
            expectedversion = datas[3]

            if expectedversion.startswith('Version: '):
                return expectedversion.split()[1]
            else:
                return [x.split()[1] for x in datas if x.startswith("Version: ")][0]
        except:
            pass


def main():
    if not sys.version_info >= (3, 5):
        print("[PB] Python 3.5+ is required. This version is %s" % sys.version.split()[0])
        print("Attempting to locate python 3.5...")

        pycom = None


        if sys.platform.startswith('win'):
            try:
                subprocess.check_output('py -3.5 -c "exit()"', shell=True)
                pycom = 'py -3.5'
            except:

                try:
                    subprocess.check_output('python3 -c "exit()"', shell=True)
                    pycom = 'python3'
                except:
                    pass

            if pycom:
                print("\nPython 3.5 found.  Re-starting PlasmaBot using: ")
                print("  %s run.py\n" % pycom)
                os.system('start cmd /k %s run.py' % pycom)
                sys.exit(0)

        else:
            try:
                pycom = subprocess.check_output(['which', 'python3.5']).strip().decode()
            except:
                pass

            if pycom:
                print("\nPython 3.5 found.  Re-starting PlasmaBot using: ")
                print("  %s run.py\n" % pycom)

                os.execlp(pycom, pycom, 'run.py')

        print("Please run the bot using Python3.5")
        input("Press ENTER to continue . . .")

        return

    import asyncio

    tried_requirementstxt = False
    tryagain = True

    loops = 0
    max_wait_time = 60

    while tryagain:

        try:
            from plasmaBot import PlasmaBot

            m = PlasmaBot()
            print("[PB] Connecting to Discord...", end='', flush=True)
            m.run()

        except KeyboardInterrupt:
            print("\n[PB] Shutting Down...\n\nThanks for using PlasmaBot!")
            m.shutdown()
            break

        except SyntaxError:
            traceback.print_exc()
            break

        except ImportError as e:
            if not tried_requirementstxt:
                tried_requirementstxt = True

                # TODO: Better output
                print(e)
                print("[PB] Attempting to install PlasmaBot dependencies...")

                err = PIP.run_install('--upgrade -r requirements.txt')

                if err:
                    print("\nYou should %s to install the PlasmaBot dependencies." %
                          ['use sudo', 'run as admin'][sys.platform.startswith('win')])
                    break
                else:
                    print("\nDependencies Installed\n")
            else:
                traceback.print_exc()
                print("[PB] Unknown ImportError, closing.")
                break

        except Exception as e:
            if hasattr(e, '__module__') and e.__module__ == 'plasmabot.exceptions':
                if e.__class__.__name__ == 'HelpfulError':
                    print(e.message)
                    break

                elif e.__class__.__name__ == "TerminateSignal":
                    break

                elif e.__class__.__name__ == "RestartSignal":
                    loops = -1
            else:
                traceback.print_exc()

        finally:
            asyncio.set_event_loop(asyncio.new_event_loop())
            loops += 1

        print("Cleaning up... ", end='')
        gc.collect()
        print("Done.")

        sleeptime = min(loops * 2, max_wait_time)
        if sleeptime:
            print("Restarting in {} seconds...".format(loops*2))
            time.sleep(sleeptime)


if __name__ == '__main__':
    main()
