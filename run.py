import os
import gc
import sys
import time
import signal
import subprocess
import traceback
import importlib

from utils.state import BotState, get_state, update_state, FatalException
from utils.tools import PIP, press_continue

# PlasmaBot Startup Sequence
# Performs compatibility checks, initializes terminal interface
def startup():
    # Check for Python 3.8+
    if not sys.version_info >= (3,12): # Not found, search for appropriate install
        print('Unsupported Python Version!')
        print('PlasmaBot requires Python 3.12+. Searching for a valid version...')

        try:
            from packaging import version # Assists in version checking for 3.10+
        except:
            PIP.run_install('packaging') # Attempt Install
            time.sleep(5) # Wait for install
            try:
                from packaging import version
            except:
                print('\nNo Supported Version Located...')
                print('Please restart PlasmaBot using Python3.12 or greater.')

        time.sleep(3) # Wait three seconds to give user time to read warning

        # Search for appropriate Python Install
        if sys.platform.startswith('win'):
            potential_operators = [
                'python',
                'python3.12', 'python312', 'py -3.12']
            valid_operator = None

            for operator in potential_operators: # Iterate over potential operators and check if valid
                try:
                    operator_version = version.parse(
                        subprocess.check_output('{} --version'.format(operator), shell=True).strip().decode().split()[1]
                    )
                    
                    if operator_version >= version.parse('3.12.0'):
                        valid_operator = operator
                        break
                except:
                    pass

            if valid_operator: # Valid Install Found!
                print('\nSupported Version Found!')
                print('Please run PlasmaBot with:"{} run.py"\n\n'.format(valid_operator))
                print('Press any key to restart PlasmaBot with this version...')
                press_continue() # Wait for User Input
                os.system('start cmd /k {0} run.py -m')
                sys.exit(0) 

        else:
            potential_operators = ['python', 'python3.12']

            for operator in potential_operators: # Iterate over potential operators
                try:
                    # Find path of current operator in list
                    valid_operator = subprocess.check_output('which {}'.format(operator), shell=True).strip().decode()

                    # Check Python Version
                    operator_version = version.parse(
                        subprocess.check_output('{} --version'.format(valid_operator), shell=True).strip().decode().split()[1]
                    )

                    # Disqualify install if version requirements not mets
                    if not (operator_version >= version.parse('3.8.0')):
                        valid_operator=None

                    # Valid Install Found!
                    if valid_operator:
                        print('\nSupported Version Found!')
                        print('Please run PlasmaBot with:"{} run.py"\n\n'.format(valid_operator))
                        print('Press any key to restart PlasmaBot with this version...')
                        press_continue() # Wait for User Input
                        os.execlp(valid_operator, valid_operator, 'run.py')
                except:
                    pass
        
        print('\nNo Supported Version Found...')
        print('Please restart PlasmaBot using Python3.12 or greater.')
        return

    # Check for Requirements and load Interface
    try:
        from rich.live import Live
    except ImportError:
        attempt_install_requirements()
        from rich.live import Live

    from plasmaBot.interface import terminal, Popup

    # Start Terminal Interface
    with Live(
        terminal.renderable, 
        screen=True, 
        refresh_per_second=10, 
        redirect_stdout=True, 
        redirect_stderr=True
    ) as live:
        terminal.store_live_instance(live) # Store live instance for future

        # Import Client
        import asyncio
        import plasmaBot

        client = None

        attempt_restart = True
        error_count = 0
        max_restart_pause_period = 60
        last_traceback_type = ''
        last_traceback_content = ''

        while attempt_restart:
            try:
                importlib.reload(plasmaBot) # Reload Bot
                client = plasmaBot.Client() # Load Client
                client.initiate()           # Start Client

            except (KeyboardInterrupt, SystemExit):
                if client:
                    asyncio.create_task(client.shutdown) # Shutdown
            
            except (SyntaxError):
                last_traceback_type = 'Syntax Error'
                last_traceback_content = traceback.format_exc()

            except ImportError as import_error:
                terminal.update_renderable(
                    Popup(
                        'Please resolve the following missing dependency:\n[red]{}[/red]'.format(import_error)+
                        '\n\n[italic]Press any key to continue...[/italic]',
                        title='[red]Missing Dependency[/red]'
                    )
                )
                press_continue() # Wait for user input
                return
                
            except FatalException as err: # Fatal Error - display error and quit
                terminal.update_renderable(Popup(err.message(), title='[red]{}[/red]'.format(err.title())))
                press_continue() # Wait for user input
                return
            
            except:
                last_traceback_type = 'Uncaught Exception'
                last_traceback_content = traceback.format_exc()

                try:
                    loop = asyncio.get_event_loop() 

                    # Handle finishing asynchronous tasks and closing asyncio loop if running
                    if loop.is_running():
                        scheduled_tasks = []

                        for task in asyncio.all_tasks():
                            if task is not asyncio.current_task():
                                scheduled_tasks.append(task)
                                task.cancel()

                        asyncio.gather(*scheduled_tasks)
                        asyncio.get_event_loop().stop()
                except:
                    terminal.update_renderable(
                        Popup(
                            f'[red]{traceback.format_exc()}[/red]',
                            title='[red]Fatal Error[/red]'
                        )
                    )
                    press_continue() # Wait for user input
                    return

            # Remove Signal Handlers
            try:
                loop = asyncio.get_event_loop()
                for s in (signal.SIGQUIT, signal.SIGTERM, signal.SIGINT):
                    loop.remove_signal_handler(s)
            except:
                pass

            try: # Handle graceful shutdown during restart process
                state = get_state() # Get current Power State

                # Handle Bot Relaunch Behavior based on Power State
                if state == BotState.RESTART:
                    os.execv(sys.executable, [__file__] + sys.argv) # Restart Process
                elif state == BotState.SHUTDOWN:
                    break # Shutdown

                # Prepare Client for Automatic Relaunch
                update_state(BotState.OFFLINE)
                client = None

                # Launch New Event Loop
                asyncio.set_event_loop(asyncio.new_event_loop())

                # Handle Restart Timer
                error_count += 1
                restart_period = min(error_count*2+3, max_restart_pause_period)

                if restart_period:
                    while restart_period > 0:
                        terminal.update_renderable(
                            Popup(
                                '[red]{}[/red]\n\n[italic]Automatically Restarting in {} seconds...[/italic]'.format(
                                    last_traceback_content, restart_period
                                ), title=last_traceback_type, justify='left'
                            )
                        )
                        time.sleep(1)
                        restart_period-=1

                # Run Garbage Collector
                gc.collect()

            except KeyboardInterrupt: # If Exception in restart code, shutdown
                return
    
def attempt_install_requirements():
    """Attempt to install library dependencies with PIP"""
    pip_error = PIP.install_requirements()

    if pip_error:
        platform_method = ['use "sudo" to run this script', 'run this script as administrator'][sys.platform.startswith('win')]
        print('Dependencies could not be installed. Please install them manually with "pip install -r requirements.txt" or {} to try again.'.format(platform_method))
        sys.exit(0)
    else:
        print('Successfully installed dependencies!')

# If `run.py` ran directly, run startup()
if __name__ == '__main__':
    startup()