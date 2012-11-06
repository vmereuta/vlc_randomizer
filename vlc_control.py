#!/usr/local/bin/python2.7
# encoding: utf-8
'''
vlc.vlc_control -- Controls a local VLC instance via the telnet controller

To run, first startup VLC, load the movies into a playlist and select VLC/Add Interface/Telnet from the menu

@author:     Vlad
        
@copyright:  2012 banoffee.net. All rights reserved.
        
@license:    Apache Software License 2.0

@contact:    vlad@banoffee.net
@deffield    updated: Updated
'''

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2012-10-22'
__updated__ = '2012-10-24'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

import random
import time


VLC_HOST = "localhost"
VLC_PORT = 4212
VLC_PASS = "admin"

## You can enter the interval in seconds as the second command line argument as well
INTERVAL_IN_SECONDS = 2 * 60
INTERVAL_IN_SECONDS = 15 
PRE_POST_OFFSET = 8 * 60


import telnetlib
## Sends an arbitrary command to VLC
def run_vlc_command(cmd, host=VLC_HOST, port=VLC_PORT, passwd=VLC_PASS):
    print("Running VLC command:", cmd)
    t = telnetlib.Telnet(host=host, port=port)
    t.read_until(b"Password: ")
    t.write(passwd.encode('ascii') + b"\n")
    
    t.read_until(b"> ")
    t.write(cmd.encode('ascii') + b"\n")
    result = t.read_until(b"> ").decode('ascii')
    t.close()
    result = result.replace('> ', '')
    print("returning:", result)
    return result 


def vlc_manipulation_logic(ignore_s, play_s, host, port, passwd):
    files_in_playlist = [f for f in run_vlc_command("playlist 2").splitlines()[1:-1]]
    playlist_id_offset = int(files_in_playlist[0].split()[1]) - 1
    print ("Got playlist contents for", len(files_in_playlist), "movies", files_in_playlist)
    ## Loop forever
    while True:
        #run_vlc_command("stop")
        #time.sleep(1)
        
        ## Choose a random movie from the playlist
        playlist_item_no = random.randint(1, len(files_in_playlist))
        print("Trying to play", files_in_playlist[playlist_item_no - 1])
        run_vlc_command("goto " + str(playlist_item_no + playlist_id_offset))
        
        length_retries = 5
        current_file_length_sec = 0
        while length_retries > 0 and current_file_length_sec == 0:
            length_retries-= 1
            time.sleep(1)
            current_file_length_sec = int(run_vlc_command("get_length"))    

        
        if current_file_length_sec == 0:
            print("0 length for", files_in_playlist[playlist_item_no - 1])
            continue

        start_time = random.randint(ignore_s, current_file_length_sec - play_s - ignore_s);
        run_vlc_command("seek " + str(start_time))
        while run_vlc_command("is_playing") == "0":
            print("Waiting...")
            time.sleep(1)
    
        ## Wait until the interval expires
        time.sleep(play_s)   
        #run_vlc_command("stop")   


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by user_name on %s.
  Copyright 2012 organization_name. All rights reserved.
  
  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-i", "--ignore", dest="ignore", type=int, default=PRE_POST_OFFSET, help="Number of seconds from the beginning/end that do not get counted [default: %(default)s]")
        parser.add_argument("-p", "--play", dest="play", type=int, default=INTERVAL_IN_SECONDS, help="Number of seconds to play from each movie [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        
        # Process arguments
        args = parser.parse_args()
        
        vlc_manipulation_logic(args.ignore, args.play, VLC_HOST, VLC_PORT, VLC_PASS)
        return 0
    
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-h")
        sys.argv.append("-v")
        sys.argv.append("-r")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'vlc.vlc_control_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())