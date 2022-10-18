import logging
from argparse import ArgumentParser
from typing import Dict, Any

from daemon import DaemonContext
from os import getgid, getuid, nice
from subprocess import Popen, PIPE, STDOUT
from sys import stderr, stdout, version_info
from time import sleep
from pulsectl import Pulse
from evdev import InputDevice, categorize, ecodes, list_devices

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
        parser.add_argument('-t', '--toggle',
                            dest='TOGGLE',
                            default=False,
                            help=f'toggle mute/unmute of all sources directly and exit',
                            action='store_true')
        parser.add_argument('-m', '--mute',
                            dest='MUTE',
                            default=False,
                            help=f'mute all sources directly and exit',
                            action='store_true')
        parser.add_argument('-u', '--unmute',
                            dest='UNMUTE',
                            default=False,
                            help=f'unmute all sources directly and exit',
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

    def _set_led(self, send_int: int) -> int:
        send_chars = str(send_int) + '\n'
        led_state_file = '/sys/class/leds/platform::micmute/brightness'
        process = Popen(['sudo', 'tee', led_state_file], stdout=PIPE, stdin=PIPE, stderr=STDOUT, text=True)
        log.debug(f"Sending {send_int} to {led_state_file}")
        result = process.communicate(input=send_chars)[0]
        log.debug(f"Process: {process}, Result: {result}")
        return process.returncode

    def _get_sources(self, pulse: Pulse) -> Dict[int, Any]:
        sources = {}
        for source in pulse.source_list():
            sources.update({source.index: source})
        return sources

    def _get_volumes(self, pulse: Pulse) -> Dict[int, Any]:
        volumes = {}
        for source in self._get_sources(pulse).values():
            volumes.update({source.index: pulse.volume_get_all_chans(source)})
        return volumes

    def mute(self, pulse: Pulse) -> int:
        for source in self._get_sources(pulse).values():
            log.info(f"Muting source {source.index}")
            pulse.volume_set_all_chans(source, self._get_volumes(pulse)[int(source.index)])
            pulse.mute(source, mute=True)

        log.info(f"Turning on mute-mic indicator led")
        return self._set_led(1)

    def unmute(self, pulse) -> int:
        for source in self._get_sources(pulse).values():
            log.info(f"Unmuting source {source.index}")
            pulse.volume_set_all_chans(source, self._get_volumes(pulse)[int(source.index)])
            pulse.mute(source, mute=False)

        log.info(f"Turning off mute-mic indicator led")
        return self._set_led(0)

    def sources(self, pulse) -> int:
        for source in self._get_sources(pulse).values():
            if source.mute == 1:
                state = 'muted'
            else:
                state = 'unmuted'

            print(f"Source index {source.index}: \"{source.description}\" ({state})")

        return 0

    def toggle(self, pulse) -> int:
        mute_counter = 0
        for source in self._get_sources(pulse).values():
            mute_counter += source.mute

        if mute_counter > 0:
            return self.unmute(pulse)
        else:
            return self.mute(pulse)

    def loop(self, pulse):
        # Make sure we're connected and wait for it.
        pulse.connect(wait=True)

        # By default, unmute input sources.
        log.info("Unmuting sources before entering event loop")
        self.unmute(pulse)

        # Determine event input device.
        thinkpad_evdev_name = "ThinkPad Extra Buttons"
        thinkpad_micmute_event_code = 248
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:
            if device.name == thinkpad_evdev_name:
                log.info(f"Monitoring keypresses from {device.path} ({device.name})..")
                for event in device.read_loop():
                    if event.type == ecodes.EV_KEY and event.code == thinkpad_micmute_event_code and event.value == 1:
                        self.toggle(pulse)

        # Error out if we did not find a thinkpad extra buttons input.
        if 'watch' not in locals():
            log.error(f"Could not find an event input device matching \"{thinkpad_evdev_name}\"")
            exit(1)

    def run(self):
        # Show list of sources.
        if self.args.SOURCES:
            exit(self.sources(Pulse()))

        # Toggle mute/unmute directly.
        if self.args.TOGGLE:
            exit(self.toggle(Pulse()))

        # Mute directly.
        if self.args.MUTE:
            exit(self.mute(Pulse()))

        # Unmute directly.
        if self.args.UNMUTE:
            exit(self.unmute(Pulse()))

        # Run main loop, backgrounded or foregrounded.
        if self.daemonize:
            log.info("Running in background (daemon) mode")
            with DaemonContext(uid=getuid(), gid=getgid(), stdout=stdout, stderr=stderr):
                self.loop(Pulse(connect=False))
        else:
            log.info("Running in foreground mode")
            self.loop(Pulse(connect=False))
