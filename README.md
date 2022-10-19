# tpmmld

`tpmmld` is the *ThinkPad Mute-Mic Light Daemon*. If you have a certain
ThinkPad where you have a mute-mic indicator led on the `F4` button, this
daemon will control it, based on the current PulseAudio mute state of all
input sources (So all input sources mute, all input sources unmute).

You can directly `mute`, `unmute` or `toggle` the mute states of all sources
by using the `-m`, `-u` or `-t` arguments. This mode is essentially a one-shot
where the process exits after doing the requested state change.

When no options are specified (run as daemon in foreground) or when passing
`-d` to run in background (daemonized), `tpmmld` will monitor the *ThinkPad
Extra Buttons* input device to keypresses (specifically, key event `248`, the
`micmute` button).

## Prerequisites

1. To read input from the micmute key, you need to be a member of the `input`
   group, or specifically, whichever group owns the device files under the
   `/dev/input` directory.

2. To enable/disable the led, the `sudo` and `tee` commands are used.
   You have to configure `sudo` in such a way that you can run `echo 1 | sudo
   tee /sys/class/leds/platform\:\:micmute/brightness` non-interactively
   (i.e., without a password prompt).

## Install

`tpmmld` is published in [pypi](https://pypi.org/project/tpmmld), so you can
simply install using `pip`:

```shell
pip install tpmmld
```

However, If it's not available there for whatever reason, or if you would like
to run it from source, you can also get it going yourself, directly from the
git repository:

```shell
git clone https://github.com/rubin55/tpmmld
cd tpmmld
python -m venv .venv
pip instal -r requirements.txt
bin/tpmmld.sh -s # shows available input source devices, with index number
bin/tpmmld.sh -t # toggle mute state on/off
bin/tpmmld.sh -m # explicitly mute all sources
bin/tpmmld.sh -u # explicitly unmute all sources
bin/tpmmld.sh    # run tpmmld in foreground
bin/tpmmld.sh -d # run tpmmld in background
```

## Usage

```text
$ tpmmld -h
usage: tpmmld [-h] [-d] [-s] [-t] [-m] [-u] [-l {INFO,ERROR,WARNING,DEBUG}]
              [-v]

options:
  -h, --help            show this help message and exit
  -d, --daemonize       run in background (daemonized mode). If not specified,
                        the process will run in the foreground output to stdin
  -s, --sources         show list of sources, with index numbers
  -t, --toggle          toggle mute/unmute of all sources directly and exit
  -m, --mute            mute all sources directly and exit
  -u, --unmute          unmute all sources directly and exit
  -l {INFO,ERROR,WARNING,DEBUG}, --loglevel {INFO,ERROR,WARNING,DEBUG}
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

## Deploy

I use [twine](https://pypi.org/project/twine) to publish `tpmmld` on pypi. To
deploy, make sure you first run the build stage. After that you can deploy the
artifacts in the `dist` directory as follows:

```shell
twine upload dist/*
```

Note that you need valid for this project pypi credentials to do so .
