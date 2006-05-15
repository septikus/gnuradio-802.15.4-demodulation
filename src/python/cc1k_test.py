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
from gnuradio.ucla_blks import cc1k_sos_pkt
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import math

from gnuradio.wxgui import stdgui, fftsink, scopesink
import wx

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
        
    
class fsk_rx_graph (stdgui.gui_flow_graph):
    st = stats()

    def __init__(self, frame, panel, vbox, argv):
        stdgui.gui_flow_graph.__init__ (self, frame, panel, vbox, argv)

        parser = OptionParser (option_class=eng_option)
        parser.add_option("-R", "--rx-subdev-spec", type="subdev", default=None,
                          help="select USRP Rx side A or B (default=first one with a daughterboard)")
        parser.add_option ("-c", "--cordic-freq", type="eng_float", default=434845200,
                           help="set Tx cordic frequency to FREQ", metavar="FREQ")
        parser.add_option ("-r", "--data-rate", type="eng_float", default=38400)
        parser.add_option ("-f", "--filename", type="string",
                           default="rx.dat", help="write data to FILENAME")
        parser.add_option ("-g", "--gain", type="eng_float", default=0,
                           help="set Rx PGA gain in dB [0,20]")
        parser.add_option ("-N", "--no-gui", action="store_true", default=False)

        (options, args) = parser.parse_args ()
        print "cordic_freq = %s" % (eng_notation.num_to_str (options.cordic_freq))

        # ----------------------------------------------------------------

        self.data_rate = options.data_rate
        self.samples_per_symbol = 8
        self.usrp_decim = int (64e6 / self.samples_per_symbol / self.data_rate)
        self.fs = self.data_rate * self.samples_per_symbol
        payload_size = 128             # bytes

        print "data_rate = ", eng_notation.num_to_str(self.data_rate)
        print "samples_per_symbol = ", self.samples_per_symbol
        print "usrp_decim = ", self.usrp_decim
        print "fs = ", eng_notation.num_to_str(self.fs)

        max_deviation = self.data_rate / 4
    
        u = usrp.source_c (0, self.usrp_decim)
        if options.rx_subdev_spec is None:
            options.rx_subdev_spec = pick_subdevice(u)
        u.set_mux(usrp.determine_rx_mux_value(u, options.rx_subdev_spec))

        subdev = usrp.selected_subdev(u, options.rx_subdev_spec)

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
        gain_mu = 0.002*self.samples_per_symbol
        self.packet_receiver = cc1k_sos_pkt.cc1k_demod_pkts(self,
                                                        callback=self.rx_callback,
                                                        sps=self.samples_per_symbol,
                                                        symbol_rate=self.data_rate,
                                                        p_size=payload_size,
                                                        threshold=-1)

        self.connect(u, self.packet_receiver)
            
        if 0 and not(options.no_gui):
            fft_input = fftsink.fft_sink_c (self, panel, title="Input", fft_size=512, sample_rate=self.fs)
            self.connect (u, fft_input)
            vbox.Add (fft_input.win, 1, wx.EXPAND)

        #send a packet...


    def rx_callback(self, ok, payload):
        self.st.npkts += 1
        if ok:
            self.st.nright += 1
        if len(payload) <= 16:
            print "ok = %5r  %d/%d" % (ok, self.st.nright, self.st.npkts)
            print "  payload: " + str(map(hex, map(ord, payload)))
            print " ------------------------"
        else:
            (pktno,) = struct.unpack('!H', payload[0:2])
            print "ok = %5r  pktno = %4d  len(payload) = %4d  %d/%d" % (ok, pktno, len(payload),
                                                                        self.st.nright, self.st.npkts)

class transmit_path:
    def __init__(self, fg, subdev_spec, bitrate, interp, spb, bt, log_p=False):

        self.normal_gain = 8000

        #self.u = usrp.sink_c()
        #dac_rate = self.u.dac_rate();

        (self._bitrate, self._spb, self._interp) = pick_tx_bitrate(bitrate, spb,
                                                                   interp, dac_rate)
        #self.u.set_interp_rate(self._interp)

        # determine the daughterboard subdevice we're using
        #if subdev_spec is None:
        #    subdev_spec = usrp.pick_tx_subdevice(self.u)
        #self.u.set_mux(usrp.determine_tx_mux_value(self.u, subdev_spec))
        #self.subdev = usrp.selected_subdev(self.u, subdev_spec)
        #print "Using TX d'board %s" % (self.subdev.side_and_name(),)

        # transmitter
        self.packet_transmitter = cc1k_sos_pkt.cc1k_mod_pkts(fg, spb=self._spb, bt=bt, msgq_limit=2)
        self.amp = gr.multiply_const_cc (self.normal_gain)
        self.filesink = gr.filesink_c('rx_test.dat')
        
        fg.connect(self.packet_transmitter, self.amp, self.filesink)
        #gr.hier_block.__init__(self, fg, None, None)

        #self.set_gain(self.subdev.gain_range()[1])  # set max Tx gain
        #self.set_auto_tr(True)                      # enable Auto Transmit/Receive switching

    def set_freq(self, target_freq):
        """
        Set the center frequency we're interested in.

        @param target_freq: frequency in Hz
        @rypte: bool

        Tuning is a two step process.  First we ask the front-end to
        tune as close to the desired frequency as it can.  Then we use
        the result of that operation and our target_frequency to
        determine the value for the digital up converter.  Finally, we feed
        any residual_freq to the s/w freq translater.
        """
        r = self.u.tune(self.subdev._which, self.subdev, target_freq)
        if r:
            # Could use residual_freq in s/w freq translator
            return True

        return False

    def set_gain(self, gain):
        self.gain = gain
        self.subdev.set_gain(gain)

    def set_auto_tr(self, enable):
        return self.subdev.set_auto_tr(enable)
        
    def send_pkt(self, payload='', eof=False):
        return self.packet_transmitter.send_pkt(payload, eof)
        
    def bitrate(self):
        return self._bitrate

    def spb(self):
        return self._spb

    def interp(self):
        return self._interp


def main ():
    tx = transmit_path()
    
    app = stdgui.stdapp (fsk_rx_graph, "FSK Rx")
    app.MainLoop ()

if __name__ == '__main__':
    # insert this in your test code...
    #import os
    #print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    #raw_input ('Press Enter to continue: ')
    
    main ()
