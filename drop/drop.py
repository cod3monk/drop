#!/usr/bin/env python
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import sys
import tempfile
import subprocess
import os
import hashlib
import base64
import shutil
from datetime import datetime
try:
    # Python 3 only
    from configparser import SafeConfigParser
except ImportError:
    # Python 2 only
    from ConfigParser import SafeConfigParser
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

try:
    import pyperclip
    clipboard = True
except ImportError:
    clipboard = False

def upload(localpath, remoteserver, remotepath, recursive=False):
    cmd = ['scp', '-pq']
    cmd[-1] += 'r'
    cmd += [localpath, remoteserver+':'+remotepath]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(' '.join(cmd))
        print("SCP failed, this has mainly these reasons: remote directory not present, scp " +
              "command invalid or unable to login.", file=sys.stderr)
        sys.exit(1)


def check_config(cfg):
    # TODO
    pass


def main():
    parser = argparse.ArgumentParser(description='Uploads data to a remote www directory via scp '
                                     'and returns a public url.')
    parser.add_argument('--destination', '-d', nargs=1,
                        help='Name of destination as found in configuration file.')
    parser.add_argument('--list-destinations', '-l', action='store_true',
                        help='List all destinations defined in configuration file.')
    parser.add_argument('infile', nargs='+', type=argparse.FileType('rb'), default=sys.stdin,
                        help='File to upload. If multiple are passed, they will be archived and '
                             'compressed before uploading.')
    parser.add_argument('--preserve-name', '-p', action='store_true',
                        help='Will preserve original filename at remote location, by adding an '
                             'intermediate directory.')
    parser.add_argument('--extension', '-e', nargs=1, required=False,
                        help='Overwrites extension on uploaded file.')
    parser.add_argument('--config-file', '-c', required=False, type=argparse.FileType('r'))
    parser.add_argument('--test', action='store_true', help='Runs a test on destination.')
    args = parser.parse_args()

    cfg = SafeConfigParser()
    cfg.read(['defaults.cfg'])
    cfg.read([os.path.expanduser('~/.drop.cfg'), '/etc/drop.cfg'])
    if args.config_file:
        cfg.readfp(args.config_file)
    check_config(cfg)
    
    # Gather all possible destinations from configuration file
    all_destiantions = cfg.sections()
    
    # Flag to be set if archive should be deleted after upload
    remove_archive_file = False

    # Create temporary test file with timestamp
    if args.test:
        args.infile = [tempfile.NamedTemporaryFile()]
        test_data = ('TEST '+str(datetime.now())+'\n').encode('utf-8')
        args.infile[0].write(test_data)
        args.infile[0].seek(0)
        args.extension = ['test']

    # List all destinations:
    if args.list_destinations:
        for s in all_destiantions:
            if s == cfg.get('DEFAULT', 'destination'):
                s += " (default)"
            print(s)
        sys.exit(0)

    # Check and select destination
    destination = None
    if not args.destination:
        # Get default destination from config
        destination = cfg.get('DEFAULT', 'destination')
    elif cfg.has_section(args.destination[0]):
        # Found perfect fit
        destination = args.destination[0]
    else:
        # Select best fitting destination, if available
        possible_dests = filter(lambda d: d.startswith(args.destination[0]), all_destiantions)
        assert possible_dests, "Could not find destination section in config."
        assert len(possible_dests) == 1, "Could not find unique destination section in config."
        destination = possible_dests[0]
    
    # Handle multiple files or directories
    if len(args.infile) >= 2:
        # Create temporary folder as base_dir for archive
        tmp_base_dir = tempfile.mkdtemp()
        try:
            for f in args.infile:
                f.close()
                file_name = os.path.split(f.name)[1]
                shutil.copyfile(f.name, os.path.join(tmp_base_dir, file_name))
            archive = shutil.make_archive(tmp_base_dir, 'zip', tmp_base_dir)
            original_file = open(archive, 'rb')
            remove_archive_file = archive
        except Exception as e:
            raise
        finally:
            shutil.rmtree(tmp_base_dir)
    else:
        original_file = args.infile[0]

    # Get extension before it is overwritten
    ext = os.path.splitext(original_file.name)[1]
    
    if args.preserve_name:
        assert len(args.infile) == 1, "--preserve-name / -p is not supported with multiple files."
        assert not args.extension, "extension is always preserved with name."
        tmp_base_dir = tempfile.mkdtemp()
        try:
            original_file_name = os.path.split(original_file.name)[1]
            temp_infilename = os.path.join(tmp_base_dir, original_file_name)
            shutil.copyfile(original_file.name, temp_infilename)
            #if cfg.has_option(args.destination[0], 'chmod'):
            chmod = cfg.getint(destination, 'chmod')
            os.chmod(temp_infilename, chmod)
            os.chmod(tmp_base_dir, chmod+73)  # Make directory executable for owner, group and user
        
            # Get remote location
            remoteserver = cfg.get(destination, 'remoteserver')
            remotedir = cfg.get(destination, 'remotedir')
        
            # Generate hash for uploaded filename
            hash_ = hashlib.sha1(original_file.read())
            original_file.close()
            hashstr = base64.urlsafe_b64encode(hash_.digest()).decode('utf-8')
            hashstr = hashstr[:cfg.getint(destination, 'hashlength')]
        
            assert '/' not in ext, "extension may not contain any slashes."
        
            upload(tmp_base_dir, remoteserver, os.path.join(remotedir, hashstr), recursive=True)

            url = cfg.get(destination, 'url')+hashstr+'/'+original_file_name
        except Exception as e:
            raise
        finally:
            shutil.rmtree(tmp_base_dir)
    else:
        # Copy into a tempfile, so we can have chmod applied
        temp_infile = tempfile.NamedTemporaryFile()
        data = original_file.read()
        original_file.close()
        if hasattr(original_file, 'encoding') and original_file.encoding:
            data = data.encode(original_file.encoding)
        temp_infile.write(data)
        temp_infile.seek(0)
        #if cfg.has_option(args.destination[0], 'chmod'):
        chmod = cfg.getint(destination, 'chmod')
        os.chmod(temp_infile.name, chmod)
        
        # Get remote location
        remoteserver = cfg.get(destination, 'remoteserver')
        remotedir = cfg.get(destination, 'remotedir')
        
        # Generate hash for uploaded filename
        hash_ = hashlib.sha1(temp_infile.read())
        hashstr = base64.urlsafe_b64encode(hash_.digest()).decode('utf-8')
        hashstr = hashstr[:cfg.getint(destination, 'hashlength')]
        
        # Choose extension for uploaded file
        if args.extension:
            ext = '.'+args.extension[0]
        remotefilename = hashstr+ext
        
        assert '/' not in ext, "extension may not contain any slashes."
        
        upload(temp_infile.name, remoteserver, os.path.join(remotedir, remotefilename))

        url = cfg.get(destination, 'url')+remotefilename
    print(url)
    if clipboard:
        pyperclip.copy(url)
        print('copied to clipboard.')

    if args.test:
        remote_data = urlopen(url).read()
        if remote_data != test_data:
            print("Failure. Different data found at remote url than expected.", file=sys.stderr)
            sys.exit(1)
        else:
            print("Success. Retreived same data from url as expected.", file=sys.stderr)
    
    if remove_archive_file:
        temp_infile.close()
        os.remove(remove_archive_file)


if __name__ == '__main__':
    main()
    