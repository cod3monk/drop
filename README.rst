drop
====

Uploads data to a remote www directory via scp and returns a public url.

Install
-------
Easiest way is to install via pip::

    pip install drop

there are currently no dependencies other than python 2.7 or python 3.4.

To install manually: copy drop/drop.py to any location of your preference

Configure
---------
A configuration file is required, it can be located at /etc/drop.cfg, ~/.drop.cfg or it's location passed via command line option --config-file.

A sample config file would be::
    
    [DEFAULT]
    # reference to the default destination (section name):
    destination = hawo

    # You can set the following defaults:
    # Location of the scp command, can be relative or absolute path:
    scp = scp
    # default length (in characters) for hashfilenames (max. 28)
    hashlength = 28
    # default chmod to apply to uploaded files (already applied localy and uploaded with -p)
    # 436 this is 0o644
    chmod = 436

    # Destinations:
    [hawo]
    # remote server dns or alias from .ssh/config and may also include username (user@server):
    remoteserver = ente
    # remote directory can be relative (to home directory) or absolute:
    remotedir = public_html/d/
    # publishing url, this must represent the above directory:
    url = http://hawo.net/~sijuhamm/d/
    # all defaults can be overwritten for any destination. For example the hashlength:
    hashlength = 10

The DEFAULT section configures default values for all other sections and the default destination. All other sections are so called destination sections. They can be selected via the --destination command line parameter.


Usage
-----
You can pase a file by argument::

    $ drop defaults.cfg
    http://hawo.net/~sijuhamm/d/NcT0jFb5.cfg
    
or any content via stdin::

    $ date | ./drop.py
    http://hawo.net/~sijuhamm/d/ephtK9DY

The filename at the remote location is actually a partial sha1 checksum of the file. The length of the checksum can be set in the configuration file. The extension is preserved when possible and can also be overwritten with the --extension parameter.

The full help message reads as follows::

    usage: drop [-h] [--destination DESTINATION] [--list-destinations]
                [--preserve-name] [--extension EXTENSION] [--config-file CONFIG_FILE]
                [--test] infile [infile ...]

    Uploads data to a remote www directory via scp and returns a public url.

    positional arguments:
      infile                File to upload. If multiple are passed, they will be
                            archived and compressed before uploading.

    optional arguments:
      -h, --help            show this help message and exit
      --destination DESTINATION, -d DESTINATION
                            Name of destination as found in configuration file.
      --list-destinations, -l
                            List all destinations defined in configuration file.
      --preserve-name, -p   Will preserve original filename at remote location, by
                            adding an intermediate directory.
      --extension EXTENSION, -e EXTENSION
                            Overwrites extension on uploaded file.
      --config-file CONFIG_FILE, -c CONFIG_FILE
      --test                Runs a test on destination.

TODOs
-----
Upcoming features:
 * (maybe) support for other upload destinations
 * support more compression/archiving formats
