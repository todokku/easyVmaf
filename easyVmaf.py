"""
MIT License

Copyright (c) 2020 Gabriel Davila - gdavila.revelo@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import  argparse
import json
import sys
import os.path
import glob



from statistics import mean
from Vmaf import vmaf
from signal import signal, SIGINT

def handler(signal_received, frame):
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    sys.exit(0)

def get_args():
    '''This function parses and return arguments passed in'''
    parser = MyParser(prog = 'eVmaf', description = "Script to easy compute VMAF using FFmpeg. It allows to deinterlace, scale and sync Ref and Distorted video samples automatically: \
            \n\n \t Autodeinterlace: If the Reference or Distorted samples are interlaced, deinterlacing is applied\
            \n\n \t Autoscale: Reference and Distorted samples are scaled automatically to 1920x1080 or 3840x2160 depending on the VMAF model to use\
            \n\n \t Autosync: The first frames of the distorted video are used as reference to a sync look up with the Reference video. \
            \n \t \t The sync is doing by a frame-by-frame look up of the best PSNR\
            \n \t \t See [-reverse] for more options of syncing\
            \n\n As output, a json file with VMAF score is created", formatter_class=argparse.RawTextHelpFormatter)
    requiredgroup = parser.add_argument_group('required arguments')
    requiredgroup.add_argument('-d' , dest='d', type = str, help = 'Distorted video', required=True)
    requiredgroup.add_argument('-r' , dest='r', type = str, help = 'Reference video ', required=True)
    parser.add_argument('-sw', dest='sw', type = float, default = 0, help='Sync Window: window size in seconds to get a subsample of the Reference video. The sync look up will be done between the first frames of the Distorted input and this Subsample. (default=0. No sync).')
    parser.add_argument('-ss',dest='ss', type = float, default = 0, help="Sync Start Time. Time in seconds from the beginning of the Reference video from which the Sync Window will be applied. (default=0)." )
    parser.add_argument('-subsample',dest='n', type = int, default = 1, help="Specifies the subsampling of frames to speed up calculation. (default=1, None)." )
    parser.add_argument('-reverse', help="If enable, it Changes the default Autosync behaviour: The first frames of the Reference video are used as reference to sync with the Distorted one. (Default = Disable).", action = 'store_true' )
    parser.add_argument('-model', dest='model', type = str, default = "HD", help="Vmaf Model. Options: HD, 4K. (Default: HD)." )
    parser.add_argument('-phone' , help =  'It enables vmaf phone model (HD only). (Default=disable).', action = 'store_true')
    parser.add_argument('-verbose' , help =  'Activate verbose loglevel. (Default: info).', action = 'store_true')
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return parser.parse_args()

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


if __name__ == '__main__':
    signal(SIGINT, handler)

    '''reading values from cmdParser'''
    cmdParser=get_args()
    main_pattern = cmdParser.d
    reference = cmdParser.r

    ''' to avoid error negative numbers are not allowed'''
    syncWin = abs(cmdParser.sw)
    ss = abs(cmdParser.ss)
    n_subsample = abs(cmdParser.n)
    reverse = cmdParser.reverse
    model = cmdParser.model
    phone = cmdParser.phone
    verbose = cmdParser.verbose

    #Setting verbosity
    if verbose: 
        loglevel = "verbose"
    else:
        loglevel = "info"



    '''
    Distorted video path could be loaded as patterns i.e., "myFolder/video-sample-*.mp4"
    In this way, many computations could be done with just one command line.
    '''
    main_pattern = os.path.expanduser(main_pattern)
    mainFiles = glob.glob(main_pattern)


    for main in mainFiles:
        myVmaf = vmaf(main, reference, loglevel=loglevel, subsample=n_subsample, model=model)
        '''check if syncWin was set. If true offset is computed automatically, otherwise manual values are used  '''

        if syncWin > 0:
            offset, psnr = myVmaf.syncOffset(syncWin, ss, reverse)
        else:
            offset = ss
            psnr = None
            if reverse: myVmaf.offset = -offset
            else: myVmaf.offset = offset
        
        myVmaf.getVmaf()
        vmafpath = myVmaf.ffmpegQos.vmafpath
        vmafScore = []
        with open (vmafpath) as jsonFile:
            jsonData = json.load(jsonFile)
            for frame in jsonData['frames']:
                vmafScore.append(frame["metrics"]["vmaf"])
        
        print("\n \n \n \n \n ")
        print("=======================================", flush=True)
        print("VMAF computed", flush=True)
        print("=======================================", flush=True)
        print("offset: ", offset, " | psnr: ", psnr)
        print("VMAF score: ", mean(vmafScore))
        print("VMAF json File Path: ", myVmaf.ffmpegQos.vmafpath )
        print("\n \n \n \n \n ")
