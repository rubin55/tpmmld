# tpmmld

`tpmmld` is the *ThinkPad Mute-Mic Light Daemon*. If you have a certain
ThinkPad where you have a mute-mic indicator led on the `F4` button, this
daemon will control it, based on the current PulseAudio mute state.

Has an additional feature that can mute/unmute *all* inputs instead of only
the one you're monitoring.

Note: to enable/disable the led, the `sudo` and `tee` commands are used.
I'm sure there's a better way, but I didn't want this program to run with
elevated privileges itself.


## Install

Ideally:

```shell
pip install tpmmld
```

However, If it's not available there for whatever reason, you can also get
it going yourself, directly from the git repository:

```shell
git clone https://github.com/rubin55/tpmmld
cd tpmmld
python -m venv .venv
pip instal -r requirements.txt
bin/tpmmld.sh -s # shows available input source devices, with index number
bin/tpmmld-sh -i 123 # run tpmmld in foreground, monitor device 123,
```

## Usage

```text
$ bin/tpmmld.sh -h
usage: tpmmld [-h] [-a] [-d] [-i INDEX] [-s] [-l {WARNING,ERROR,INFO,DEBUG}] [-v]

options:
  -h, --help            show this help message and exit
  -a, --all             when muting, mute all available inputs, when unmuting, unmute all available inputs
  -d, --daemonize       run in background (daemonized mode). If not specified, the process will run in the
                        foreground output to stdin
  -i INDEX, --index INDEX
                        specify index of device to monitor
  -s, --sources         show list of sources, with index numbers
  -l {WARNING,ERROR,INFO,DEBUG}, --loglevel {WARNING,ERROR,INFO,DEBUG}
                        specify the loglevel to use, defaults to 'INFO'
  -v, --version         show program's version number and exit
```

## Build

Since this is a python package, you don't really need to build, but if you
would like to build the pip packages, you can do that as follows:

```shell
python -m build
```

You will then find the pip package binaries in `dist/`. You can install
them using `pip`.
