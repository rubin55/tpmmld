import logging
from argparse import ArgumentParser
from daemon import DaemonContext
from os import getgid, getuid, nice
from subprocess import Popen, PIPE, STDOUT
from sys import stderr, stdout, version_info
from time import sleep
from pulsectl import Pulse

from .version import __version__


# Default program name and logger.
program = "tpmmld"
log = logging.getLogger(program)


# Verify python version.
def verify_python_version() -> None:
    if version_info.major != 3 or version_info.minor < 8:
        log.error(f"Python version needs to be version 3, and at least 3.8, "
                  f"whilst you seem to be running {version_info.major}.{version_info.minor}. Exiting.")
        exit(1)


# Main entry.
def main() -> None:
    nice(19)
    verify_python_version()

    app = Application()
    app.run()


class Application:
    def __init__(self):
        parser = ArgumentParser(prog=program)

        parser.add_argument('-d', '--daemonize',
                            dest='DAEMONIZE',
                            default=False,
                            help='run in background (daemonized mode). If not specified, '
                                 'the process will run in the foreground output to stdin',
                            action='store_true')
        parser.add_argument('-s', '--sources',
                            dest='SOURCES',
                            default=False,
                            help=f'show list of sources, with index numbers',
                            action='store_true')
        parser.add_argument('-l', '--loglevel',
                            dest='LOGLEVEL',
                            default="info",
                            help='specify the loglevel to use, defaults to \'INFO\'',
                            choices={"DEBUG", "INFO", "WARNING", "ERROR"},
                            type=str.upper)
        parser.add_argument('-v', '--version', action='version',
                            version=f"{program} {__version__}")

        # Initialized args.
        self.args = parser.parse_args()

        # Setup logger.
        if self.args.LOGLEVEL:

            # Make sure there are no other log handlers set.
            root = logging.getLogger()
            if root.handlers:
                for handler in logging.getLogger().handlers:
                    root.removeHandler(handler)

            numeric_loglevel = getattr(logging, self.args.LOGLEVEL, None)
            if not isinstance(numeric_loglevel, int):
                raise ValueError('Invalid log level: %s' % self.args.LOGLEVEL)

            logging.basicConfig(datefmt='%Y-%m-%d %H:%M:%S',
                                format='[%(levelname)s] %(asctime)s, %(name)s: %(message)s',
                                level=numeric_loglevel,
                                stream=stderr)

        # Do we want to daemonize?
        self.daemonize = self.args.DAEMONIZE

        # The led state file.
        self.led_state_file = '/sys/class/leds/platform::micmute/brightness'

    def loop(self):
        # Initialize pulse object.
        pulse = Pulse(connect=False)

        # Connect to Pulse instance.
        pulse.connect(wait=True)

        # Put Pulse sources in an index.
        sources = {}
        for source in pulse.source_list():
            sources.update({source.index: source})

        # Show list of sources.
        if self.args.SOURCES:

            for source in sources.values():
                if source.mute == 1:
                    state = 'muted'
                else:
                    state = 'unmuted'

                print(f"Source index {source.index}: \"{source.description}\" ({state})")
            exit(0)

        # Store current volume levels.
        volume_memory = {}
        for source in sources.values():
            volume_memory.update({source.index: pulse.volume_get_all_chans(source)})

        # Initial mute state.
        initial_mute_counter = 0
        for source in sources.values():
            initial_mute_counter += source.mute

        # Previous mute state.
        previous_mute_counter = initial_mute_counter

        # Loopsy.
        initial_run = True
        while True:
            updated_mute_counter = 0
            for source in sources.values():
                updated_mute_counter += pulse.get_source_by_name(source.name).mute

            if initial_run or previous_mute_counter > updated_mute_counter:
                log.info(f"Mute counter went down, from {previous_mute_counter} to {updated_mute_counter}, unmuting all input sources:")
                for source in sources.values():
                    log.info(f"Unmuting source {source.index}")
                    pulse.volume_set_all_chans(source, volume_memory[int(source.index)])
                    pulse.mute(source, mute=False)

                log.info(f"Turning off mute-mic indicator led")
                # if path.exists(self.led_state_file) and path.isfile(self.led_state_file):
                #     with open(self.led_state_file, 'w') as f:
                #         f.write('0')
                p = Popen(['sudo', 'tee', self.led_state_file], stdout=PIPE, stdin=PIPE, stderr=STDOUT).communicate(input=b'0\n')

                # And set previous mute counter to updated mute counter.
                previous_mute_counter = updated_mute_counter

            elif previous_mute_counter < updated_mute_counter:
                log.info(f"Mute counter went up, from {previous_mute_counter} to {updated_mute_counter}, muting all input sources:")
                for source in sources.values():
                    log.info(f"Muting source {source.index}")
                    pulse.volume_set_all_chans(source, volume_memory[int(source.index)])
                    pulse.mute(source, mute=True)

                log.info(f"Turning on mute-mic indicator led")
                # if path.exists(self.led_state_file) and path.isfile(self.led_state_file):
                #     with open(self.led_state_file, 'w') as f:
                #         f.write('1')
                p = Popen(['sudo', 'tee', self.led_state_file], stdout=PIPE, stdin=PIPE, stderr=STDOUT).communicate(input=b'1\n')

                # And set previous mute counter to updated mute counter.
                previous_mute_counter = updated_mute_counter

            # Initial run only happens once.
            initial_run = False

            # Pause before re-evaluating.
            sleep(1)

    def run(self):
        # Run main loop, backgrounded or foregrounded.
        if self.daemonize:
            with DaemonContext(uid=getuid(), gid=getgid(), stdout=stdout, stderr=stderr):
                self.loop()
        else:
            self.loop()
