# tpmmld

`tpmmld` is the *ThinkPad Mute-Mic Light Daemon*. If you have a certain
ThinkPad where you have a mute-mic indicator led on the `F4` button, this
daemon will control it, based on the current PulseAudio mute state of all
input sources (So all input sources mute, all input sources unmute).

When the daemon runs, it monitors for mute state changes on any input source.
If any input source is muted, all input sources are muted by the daemon,
likewise with unmuting, if any input source is unmuted, all input sources are
unmuted.

Note: to enable/disable the led, the `sudo` and `tee` commands are used.
I'm sure there's a better way, but I didn't want this program to run with
elevated privileges itself. You have to configure `sudo` in such a way that
you can run `echo 1 | sudo tee /sys/class/leds/platform\:\:micmute/brightness`
non-interactively (i.e., without a password prompt).


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
bin/tpmmld.sh    # run tpmmld in foreground
bin/tpmmld.sh -d # run tpmmld in background
```

## Usage

```text
$ bin/tpmmld.sh -h
usage: tpmmld [-h] [-a] [-d] [-i INDEX] [-s] [-l {WARNING,ERROR,INFO,DEBUG}] [-v]

options:
  -h, --help            show this help message and exit
  -d, --daemonize       run in background (daemonized mode). If not specified, the process will run in the
                        foreground output to stdin
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
