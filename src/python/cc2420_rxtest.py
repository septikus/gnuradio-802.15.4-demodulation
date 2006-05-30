#!/usr/bin/env python

#
# Copyright (c) 2003 The Regents of the University of California.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
# 3. All advertising materials mentioning features or use of this
#    software must display the following acknowledgement:
#       This product includes software developed by Networked &
#       Embedded Systems Lab at UCLA
# 4. Neither the name of the University nor that of the Laboratory
#    may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS
# OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
# USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#


#
# Decoder of Mica2 RADIO Packets. We use the SOS operating system for Mica2s.
# Similar code should also work with TinyOS, though you would want to modify
# the packet structure in cc1k_sos_pkt.py.
#
# Modified by: Thomas Schmid
#
  
from gnuradio import gr, eng_notation
from gnuradio import usrp
from gnuradio import audio
from gnuradio import ucla
from gnuradio.ucla_blks import ieee802_15_4_pkt
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import math, struct, time

#from gnuradio.wxgui import stdgui, fftsink, scopesink
#import wx

start = 0

def pick_subdevice(u):
    """
    The user didn't specify a subdevice on the command line.
    If there's a daughterboard on A, select A.
    If there's a daughterboard on B, select B.
    Otherwise, select A.
    """
    if u.db[0][0].dbid() >= 0:       # dbid is < 0 if there's no d'board or a problem
        return (0, 0)
    if u.db[1][0].dbid() >= 0:
        return (1, 0)
    return (0, 0)

class stats(object):
    def __init__(self):
        self.npkts = 0
        self.nright = 0
        
    
class oqpsk_rx_graph (gr.flow_graph):
    def __init__(self, options, rx_callback):
        gr.flow_graph.__init__(self)
        print "cordic_freq = %s" % (eng_notation.num_to_str (options.cordic_freq))


        # ----------------------------------------------------------------

        self.data_rate = options.data_rate
        self.samples_per_symbol = 2
        self.usrp_decim = int (64e6 / self.samples_per_symbol / self.data_rate)
        self.fs = self.data_rate * self.samples_per_symbol
        payload_size = 128             # bytes

        print "data_rate = ", eng_notation.num_to_str(self.data_rate)
        print "samples_per_symbol = ", self.samples_per_symbol
        print "usrp_decim = ", self.usrp_decim
        print "fs = ", eng_notation.num_to_str(self.fs)

        u = usrp.source_c (0, self.usrp_decim)
        if options.rx_subdev_spec is None:
            options.rx_subdev_spec = pick_subdevice(u)
        u.set_mux(usrp.determine_rx_mux_value(u, options.rx_subdev_spec))

        subdev = usrp.selected_subdev(u, options.rx_subdev_spec)
        print "Using RX d'board %s" % (subdev.side_and_name(),)
        #subdev.select_rx_antenna('RX2')

        #u.set_rx_freq (0, -options.cordic_freq)
        u.tune(0, subdev, options.cordic_freq)
        u.set_pga(0, options.gain)
        u.set_pga(1, options.gain)

        filter_taps =  gr.firdes.low_pass (1,                   # gain
                                           self.fs,             # sampling rate
                                           self.data_rate / 2 * 1.1, # cutoff
                                           self.data_rate,           # trans width
                                           gr.firdes.WIN_HANN)

        print "len = ", len (filter_taps)

        #filter = gr.fir_filter_ccf (1, filter_taps)

        # receiver
        #self.file_sink = gr.file_sink(gr.sizeof_gr_complex, "/home/thomas/projects/sdr/gnuradio/gr-build/gr-ucla/src/python/oqpsk_synced_2sps.dat")
        #self.connect(u, self.file_sink)
        
        #self.u = gr.file_source(gr.sizeof_gr_complex, "/media/ramdrive/oqpsk_receive_2sps.dat")
        self.u = u
        
        #self.squelch = gr.simple_squelch_cc(50)

        self.packet_receiver = ieee802_15_4_pkt.ieee802_15_4_demod_pkts(self,
                                                                callback=rx_callback,
                                                                sps=self.samples_per_symbol,
                                                                symbol_rate=self.data_rate,
                                                                threshold=-1)

        self.squelch = gr.simple_squelch_cc(50)
        #self.file_sink = gr.file_sink(gr.sizeof_gr_complex, "/dev/null")
        self.connect(self.u, self.squelch, self.packet_receiver)
        #self.connect(self.u, self.file_sink)
        
        #send a packet...

def main ():

    def rx_callback(ok, payload):
        st.npkts += 1
        if ok:
            st.nright += 1
        if len(payload) <= 16:
            print "ok = %5r  %d/%d" % (ok, st.nright, st.npkts)
            print "  payload: " + str(map(hex, map(ord, payload)))
            print " ------------------------"
        else:
            (pktno,) = struct.unpack('!H', payload[0:2])
            print "ok = %5r  pktno = %4d  len(payload) = %4d  %d/%d" % (ok, pktno, len(payload),
                                                                        st.nright, st.npkts)
            print "  payload: " + str(map(hex, map(ord, payload)))
            print " ------------------------"

        
    parser = OptionParser (option_class=eng_option)
    parser.add_option("-R", "--rx-subdev-spec", type="subdev", default=None,
                      help="select USRP Rx side A or B (default=first one with a daughterboard)")
    parser.add_option ("-c", "--cordic-freq", type="eng_float", default=2475000000,
                       help="set rx cordic frequency to FREQ", metavar="FREQ")
    parser.add_option ("-r", "--data-rate", type="eng_float", default=2000000)
    parser.add_option ("-f", "--filename", type="string",
                       default="rx.dat", help="write data to FILENAME")
    parser.add_option ("-g", "--gain", type="eng_float", default=0,
                       help="set Rx PGA gain in dB [0,20]")
    parser.add_option ("-N", "--no-gui", action="store_true", default=False)
    
    (options, args) = parser.parse_args ()

    st = stats()

    fg = oqpsk_rx_graph(options, rx_callback)
    fg.start()
    start = time.time()

    fg.wait()

    end = time.time()

    print "time taken: %f s"%(end-start)

if __name__ == '__main__':
    # insert this in your test code...
    import os
    print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    #raw_input ('Press Enter to continue: ')
    
    main ()
