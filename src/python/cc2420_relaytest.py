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
# Decoder of IEEE 802.15.4 RADIO Packets. 
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
        print "cordic_freq = %s" % (eng_notation.num_to_str (options.cordic_freq_rx))


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

        self.subdev = usrp.selected_subdev(u, options.rx_subdev_spec)
        print "Using RX d'board %s" % (self.subdev.side_and_name(),)
        #self.subdev.select_rx_antenna('RX2')

        #u.set_rx_freq (0, -options.cordic_freq_rx)
        u.tune(0, self.subdev, options.cordic_freq_rx)
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
        
        self.set_auto_tr(True)                      # enable Auto Transmit/Receive switching

    def set_auto_tr(self, enable):
        return self.subdev.set_auto_tr(enable)

class transmit_path(gr.flow_graph):
    def __init__(self, options):
        gr.flow_graph.__init__(self)
        self.normal_gain = 8000

        self.u = usrp.sink_c()
        dac_rate = self.u.dac_rate();
        self._data_rate = 2000000
        self._spb = 2
        self._interp = int(128e6 / self._spb / self._data_rate)
        self.fs = 128e6 / self._interp

        self.u.set_interp_rate(self._interp)

        # determine the daughterboard subdevice we're using
        if options.tx_subdev_spec is None:
            options.tx_subdev_spec = usrp.pick_tx_subdevice(self.u)
        self.u.set_mux(usrp.determine_tx_mux_value(self.u, options.tx_subdev_spec))
        self.subdev = usrp.selected_subdev(self.u, options.tx_subdev_spec)
        print "Using TX d'board %s" % (self.subdev.side_and_name(),)

        self.u.tune(self.subdev._which, self.subdev, options.cordic_freq_tx)
        self.u.set_pga(0, options.gain)
        self.u.set_pga(1, options.gain)

        # transmitter
        self.packet_transmitter = ieee802_15_4_pkt.ieee802_15_4_mod_pkts(self, spb=self._spb, msgq_limit=2)
        self.gain = gr.multiply_const_cc (self.normal_gain)
        #self.filesink = gr.filesink_c('rx_test.dat')

        
        
        self.connect(self.packet_transmitter, self.gain, self.u)
        #gr.hier_block.__init__(self, fg, None, None)

        self.set_gain(self.subdev.gain_range()[1])  # set max Tx gain
        self.set_auto_tr(True)                      # enable Auto Transmit/Receive switching

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
        return self.packet_transmitter.send_pkt(0xe5, struct.pack("HHHH", 0xFFFF, 0xFFFF, 0x10, 0x10), payload, eof)

    def send_pkt(self, seqno, address, payload='', eof=False):
        return self.packet_transmitter.send_pkt(seqno, address, payload, eof)

    def bitrate(self):
        return self._bitrate

    def spb(self):
        return self._spb

    def interp(self):
        return self._interp


def main ():

        
    def rx_callback(ok, payload):
        st.npkts += 1
        if ok:
            st.nright += 1
            (pktno,) = struct.unpack('!B', payload[2:3])
            print "ok = %5r  pktno = %4d  len(payload) = %4d  %d/%d" % (ok, pktno, len(payload),
                                                                        st.nright, st.npkts)
            print "  payload: " + str(map(hex, map(ord, payload)))

            print "\nRetransmit"
            fgtx.send_pkt(pktno, payload[3:11], payload[11:len(payload)-2])
            print " ------------------------"

    #    print "send message %d:"%(i+1,)

        

    parser = OptionParser (option_class=eng_option)
    parser.add_option("-R", "--rx-subdev-spec", type="subdev", default=None,
                      help="select USRP Rx side A or B (default=first one with a daughterboard)")
    parser.add_option("-T", "--tx-subdev-spec", type="subdev", default=None,
                      help="select USRP Tx side A or B (default=first one with a daughterboard)")
    parser.add_option ("-t", "--cordic-freq-tx", type="eng_float", default=2475000000,
                       help="set Tx cordic frequency to FREQ", metavar="FREQ")
    parser.add_option ("-c", "--cordic-freq-rx", type="eng_float", default=2405000000,
                       help="set rx cordic frequency to FREQ", metavar="FREQ")
    parser.add_option ("-r", "--data-rate", type="eng_float", default=2000000)
    parser.add_option ("-f", "--filename", type="string",
                       default="rx.dat", help="write data to FILENAME")
    parser.add_option ("-g", "--gain", type="eng_float", default=0,
                       help="set Rx PGA gain in dB [0,20]")
    parser.add_option ("-N", "--no-gui", action="store_true", default=False)
    
    (options, args) = parser.parse_args ()

    st = stats()

    fgtx = transmit_path(options)
    fgtx.start()

    fgrx = oqpsk_rx_graph(options, rx_callback)
    fgrx.start()

    start = time.time()
    
    #for i in range(1000):
    #    print "send message %d:"%(i+1,)
    #    fg.send_pkt(struct.pack('9B', 0x1, 0x80, 0x80, 0xff, 0xff, 0x10, 0x0, 0x20, 0x0))
        #fg.send_pkt(struct.pack('BBBBBBBBBBBBBBBBBBBBBBBBBBB', 0x1, 0x8d, 0x8d, 0xff, 0xff, 0xbd, 0x0, 0x22, 0x12, 0xbd, 0x0, 0x1, 0x0, 0xff, 0xff, 0x8e, 0xff, 0xff, 0x0, 0x3, 0x3, 0xbd, 0x0, 0x1, 0x0, 0x0, 0x0))
        #0x1, 0x8d, 0x8d, 0xff, 0xff, 0x02, 0x0, 0x22, 0x12, 0xd6, 0x0, 0xff, 0xff, 0x8e, 0xff, 0xff, 0x0, 0x0, 0x0, 0xd6, 0x0, 0x15, 0x0, 0x0, 0x0))
    #    time.sleep(0.005)
                    
    fgrx.wait()
    fgtx.wait()
    
    end = time.time()

    print "time taken: %f s"%(end-start)

if __name__ == '__main__':
    # insert this in your test code...
    import os
    print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    #raw_input ('Press Enter to continue: ')
    
    main ()
