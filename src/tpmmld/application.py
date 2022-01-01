import logging
from argparse import ArgumentParser
from daemon import DaemonContext
from os import getgid, getuid
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
    verify_python_version()

    app = Application()
    app.run()


class Application:
    def __init__(self):
        parser = ArgumentParser(prog=program)

        parser.add_argument('-a', '--all',
                            dest='MUTE_ALL',
                            default=False,
                            help='when muting, mute all available inputs, when unmuting, '
                                 'unmute all available inputs',
                            action='store_true')
        parser.add_argument('-d', '--daemonize',
                            dest='DAEMONIZE',
                            default=False,
                            help='run in background (daemonized mode). If not specified, '
                                 'the process will run in the foreground output to stdin',
                            action='store_true')
        parser.add_argument('-i', '--index',
                            dest='INDEX',
                            default=0,
                            help=f'specify index of device to monitor')
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

        # Do we want to mute all sources?
        self.mute_all = self.args.MUTE_ALL

        # do we want to daemonize?
        self.daemonize = self.args.DAEMONIZE

        # The led state file.
        self.led_state_file = '/sys/class/leds/platform::micmute/brightness'

    def loop(self):
        # Initialize pulse object.
        pulse = Pulse()

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

        # Set source of which we monitor its mute-state.
        monitored_source = 0
        try:
            monitored_source = sources[int(self.args.INDEX)]
        except (KeyError, ValueError):
            log.error(f'Source with index {self.args.INDEX} not found, try "-s" first.')
            exit(1)

        # Store current volume levels.
        volume_memory = {}
        for source in sources.values():
            volume_memory.update({source.index: pulse.volume_get_all_chans(source)})

        # Initial mute state
        previous_mute_state = monitored_source.mute

        # Loopsy.
        while True:
            current_mute_state = pulse.get_source_by_name(monitored_source.name).mute
            if current_mute_state == 0 and previous_mute_state == 1:
                previous_mute_state = 0

                log.info(f"Source with index {monitored_source.index} was muted but became unmuted")
                if self.mute_all:
                    log.info("Additionally unmuting any other sources I have:")
                    for source in sources.values():
                        log.info(f"Unmuting source {source.index}")
                        pulse.volume_set_all_chans(source, volume_memory[int(source.index)])
                        pulse.mute(source, mute=False)

                log.info(f"Turning off mute-mic indicator led")
                # if path.exists(self.led_state_file) and path.isfile(self.led_state_file):
                #     with open(self.led_state_file, 'w') as f:
                #         f.write('0')
                p = Popen(['sudo', 'tee', self.led_state_file], stdout=PIPE, stdin=PIPE, stderr=STDOUT).communicate(input=b'0\n')

            elif current_mute_state == 1 and previous_mute_state == 0:
                previous_mute_state = 1

                log.info(f"Source with index {monitored_source.index} was unmuted but became muted")
                if self.mute_all:
                    log.info("Additionally muting any sources I have:")
                    for source in sources.values():
                        log.info(f"Muting source {source.index}")
                        volume_memory[int(source.index)] = pulse.volume_get_all_chans(source)
                        pulse.mute(source, mute=True)

                log.info(f"Turning on mute-mic indicator led")
                # if path.exists(self.led_state_file) and path.isfile(self.led_state_file):
                #     with open(self.led_state_file, 'w') as f:
                #         f.write('1')
                p = Popen(['sudo', 'tee', self.led_state_file], stdout=PIPE, stdin=PIPE, stderr=STDOUT).communicate(input=b'1\n')

            else:
                log.debug(f"Current state: {current_mute_state}")

            sleep(1)

    def run(self):
        # Run main loop, backgrounded or foregrounded.
        if self.daemonize:
            with DaemonContext(uid=getuid(), gid=getgid(), stdout=stdout, stderr=stderr):
                self.loop()
        else:
            self.loop()
