#!/usr/bin/env python

#
# Decoder of IEEE 802.15.4 RADIO Packets.
#
# Modified by: Thomas Schmid
#
  
from gnuradio import gr, eng_notation
from gnuradio import usrp
from gnuradio import ucla
from gnuradio.ucla_blks import ieee802_15_4_pkt
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import math, struct, time, sys

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

        u.tune(0, subdev, options.cordic_freq)
        u.set_pga(0, options.gain)
        u.set_pga(1, options.gain)

        self.u = u
        #self.u = gr.file_source(gr.sizeof_gr_complex, 'rx_test.dat')
        self.packet_receiver = ieee802_15_4_pkt.ieee802_15_4_demod_pkts(self,
                                                                callback=rx_callback,
                                                                sps=self.samples_per_symbol,
                                                                symbol_rate=self.data_rate,
                                                                threshold=-1)

        self.squelch = gr.pwr_squelch_cc(50, 1, 0, True)
        self.connect(self.u, self.squelch, self.packet_receiver)

class transmit_path(gr.flow_graph):
    def __init__(self, options):
        gr.flow_graph.__init__(self)
        self.normal_gain = 8000
        self.pktno = 0
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

        self.u.tune(self.subdev._which, self.subdev, options.cordic_freq)
        self.u.set_pga(0, options.gain)
        self.u.set_pga(1, options.gain)

        # transmitter
        self.packet_transmitter = ieee802_15_4_pkt.ieee802_15_4_mod_pkts(self, spb=self._spb, msgq_limit=2)
        self.gain = gr.multiply_const_cc (self.normal_gain)
        
        self.connect(self.packet_transmitter, self.gain, self.u)

        #self.filesink = gr.file_sink(gr.sizeof_gr_complex, 'rx_test.dat')
        #self.connect(self.gain, self.filesink)

        self.set_gain(self.subdev.gain_range()[1])  # set max Tx gain
        self.set_auto_tr(True)                      # enable Auto Transmit/Receive switching

    def set_gain(self, gain):
        self.gain = gain
        self.subdev.set_gain(gain)

    def set_auto_tr(self, enable):
        return self.subdev.set_auto_tr(enable)
        
    def send_pkt(self, payload='', eof=False):
        self.pktno += 1
        return self.packet_transmitter.send_pkt(self.pktno%256, struct.pack("HHHH", 0xFFFF, 0xFFFF, 0xa , 0xa), payload, eof)



def main ():
    global tsent, treceived
    
    def rx_callback(ok, payload):
        if ok and payload[7] != chr(0xa):
            treceived = time.time()
            print "Received PONG from %d, msg %s"%(ord(payload[7]), str(map(hex, map(ord, payload[-2]))))
            print "RTT: ", treceived - tsent
            (pktno,) = struct.unpack('!H', payload[0:2])
            #print "ok = %5r  pktno = %4d  len(payload) = %4d  %d/%d" % (ok, pktno, len(payload),
                                                                        #st.nright, st.npkts)
            #print "  payload: " + str(map(hex, map(ord, payload)))
            print " ------------------------"
        sys.stdout.flush()

        
    parser = OptionParser (option_class=eng_option)
    parser.add_option("-R", "--rx-subdev-spec", type="subdev", default="A",
                      help="select USRP Rx side A or B (default=first one with a daughterboard)")
    parser.add_option("-T", "--tx-subdev-spec", type="subdev", default="A",
                      help="select USRP Tx side A or B (default=first one with a daughterboard)")
    parser.add_option ("-c", "--cordic-freq", type="eng_float", default=2480000000,
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
    tx = transmit_path(options)
    tx.start()

    for i in range(100000):
        print "send message %d:"%(i+1,)
        tsent = time.time()
        tx.send_pkt(struct.pack('10B', 0x1, 0x80, 0x80, 0xff, 0xff, 0xa, 0x0, 0x20, 0x1, i%256))
#this is an other example packet we could send.
        #fg.send_pkt(struct.pack('BBBBBBBBBBBBBBBBBBBBBBBBBBB', 0x1, 0x8d, 0x8d, 0xff, 0xff, 0xbd, 0x0, 0x22, 0x12, 0xbd, 0x0, 0x1, 0x0, 0xff, 0xff, 0x8e, 0xff, 0xff, 0x0, 0x3, 0x3, 0xbd, 0x0, 0x1, 0x0, 0x0, 0x0))
        time.sleep(0.05)


    fg.wait()

if __name__ == '__main__':
    # insert this in your test code...
    #import os
    #print 'Blocked waiting for GDB attach (pid = %d)' % (os.getpid(),)
    #raw_input ('Press Enter to continue: ')
    
    main ()
