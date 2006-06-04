#
# Copyright 2005 Free Software Foundation, Inc.
# 
# This file is part of GNU Radio
# 
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
# 

# This is derived from gmsk2_pkt.py.
#
# Modified by: Thomas Schmid
#

from math import pi
import Numeric

from gnuradio import gr, packet_utils, gru
from gnuradio import ucla
import crc16
import gnuradio.gr.gr_threading as _threading
import ieee802_15_4
import struct

MAX_PKT_SIZE = 128

def make_ieee802_15_4_packet(FCF, seqNr, addressInfo, payload, pad_for_usrp=True, preambleLength=4, SFD=0xA7):
    """
    Build a 802_15_4 packet

    @param payload:
    @param pad_for_usrp:
    """

    if len(FCF) != 2:
        raise ValueError, "len(FCF) must be equal to 2"
    if seqNr > 255:
        raise ValueError, "seqNr must be smaller than 255"
    if len(addressInfo) > 20:
        raise ValueError, "len(addressInfo) must be in [0, 20]"

    if len(payload) > MAX_PKT_SIZE - 5 - len(addressInfo):
        raise ValueError, "len(payload) must be in [0, %d]" %(MAX_PKT_SIZE)

    SHR = struct.pack("BBBBB", 0, 0, 0, 0, SFD)
    PHR = struct.pack("B", 3 + len(addressInfo) + len(payload) + 2)
    MPDU = FCF + struct.pack("B", seqNr) + addressInfo + payload
    crc = crc16.CRC16()
    crc.update(MPDU)

    FCS = crc.checksum()



    pkt = ''.join((SHR, PHR, MPDU, FCS))

    if pad_for_usrp:
        # note that we have 16 samples which go over the USB for each bit
        pkt = pkt + (_npadding_bytes(len(pkt), 16) * '\x00')+5*'\x00'

    return pkt

def _npadding_bytes(pkt_byte_len, spb):
    """
    Generate sufficient padding such that each packet ultimately ends
    up being a multiple of 512 bytes when sent across the USB.  We
    send 4-byte samples across the USB (16-bit I and 16-bit Q), thus
    we want to pad so that after modulation the resulting packet
    is a multiple of 128 samples.

    @param ptk_byte_len: len in bytes of packet, not including padding.
    @param spb: samples per baud == samples per bit (1 bit / baud with GMSK)
    @type spb: int

    @returns number of bytes of padding to append.
    """
    modulus = 128
    byte_modulus = gru.lcm(modulus/8, spb) / spb
    r = pkt_byte_len % byte_modulus
    if r == 0:
        return 0
    return byte_modulus - r

def make_FCF(frameType=1, securityEnabled=0, framePending=0, acknowledgeRequest=0, intraPAN=0, destinationAddressingMode=2, sourceAddressingMode=2):
    """
    Build the FCF for the 802_15_4 packet

    """
    if frameType >= 2**3:
        raise ValueError, "frametype must be < 8"
    if securityEnabled >= 2**1:
        raise ValueError, " must be < "
    if framePending >= 2**1:
        raise ValueError, " must be < "
    if acknowledgeRequest >= 2**1:
        raise ValueError, " must be < "
    if intraPAN >= 2**1:
        raise ValueError, " must be < "
    if destinationAddressingMode >= 2**2:
        raise ValueError, " must be < "
    if sourceAddressingMode >= 2**2:
        raise ValueError, " must be < "

    
    
    return struct.pack("H", frameType
                       + (securityEnabled << 3)
                       + (framePending << 4)
                       + (acknowledgeRequest << 5)
                       + (intraPAN << 6)
                       + (destinationAddressingMode << 10)
                       + (sourceAddressingMode << 14))
    

class ieee802_15_4_mod_pkts(gr.hier_block):
    """
    CC1K modulator that is a GNU Radio source.

    Send packets by calling send_pkt
    """
    def __init__(self, fg, msgq_limit=2, pad_for_usrp=True, *args, **kwargs):
        """
	Hierarchical block for the 802_15_4 O-QPSK  modulation.

        Packets to be sent are enqueued by calling send_pkt.
        The output is the complex modulated signal at baseband.

	@param fg: flow graph
	@type fg: flow graph
        @param access_code: 64-bit sync code
        @type access_code: string of length 8
        @param msgq_limit: maximum number of messages in message queue
        @type msgq_limit: int
        @param pad_for_usrp: If true, packets are padded such that they end up a multiple of 128 samples

        See 802_15_4_mod for remaining parameters
        """
        self.pad_for_usrp = pad_for_usrp

        # accepts messages from the outside world
        self.pkt_input = gr.message_source(gr.sizeof_char, msgq_limit)
        self.ieee802_15_4_mod = ieee802_15_4.ieee802_15_4_mod(fg, *args, **kwargs)
        fg.connect(self.pkt_input, self.ieee802_15_4_mod)
        gr.hier_block.__init__(self, fg, None, self.ieee802_15_4_mod)

    def send_pkt(self, seqNr, addressInfo, payload='', eof=False):
        """
        Send the payload.

        @param payload: data to send
        @type payload: string
        """
        if eof:
            msg = gr.message(1) # tell self.pkt_input we're not sending any more packets
        else:
            # print "original_payload =", string_to_hex_list(payload)
            FCF = make_FCF()
            
            pkt = make_ieee802_15_4_packet(FCF,
                                           seqNr,
                                           addressInfo,
                                           payload,
                                           self.pad_for_usrp)
            print "pkt =", packet_utils.string_to_hex_list(pkt), len(pkt)
            msg = gr.message_from_string(pkt)
        self.pkt_input.msgq().insert_tail(msg)


class ieee802_15_4_demod_pkts(gr.hier_block):
    """
    802_15_4 demodulator that is a GNU Radio sink.

    The input is complex baseband.  When packets are demodulated, they are passed to the
    app via the callback.
    """

    def __init__(self, fg, callback=None, threshold=-1, *args, **kwargs):
        """
	Hierarchical block for O-QPSK demodulation.

	The input is the complex modulated signal at baseband.
        Demodulated packets are sent to the handler.

	@param fg: flow graph
	@type fg: flow graph
        @param access_code: 64-bit sync code
        @type access_code: string of length 8
        @param callback:  function of two args: ok, payload
        @type callback: ok: bool; payload: string
        @param threshold: detect access_code with up to threshold bits wrong (-1 -> use default)
        @type threshold: int

        See cc1k_demod for remaining parameters.
	"""

        self._rcvd_pktq = gr.msg_queue()          # holds packets from the PHY
        self.ieee802_15_4_demod = ieee802_15_4.ieee802_15_4_demod(fg, *args, **kwargs)
        self._packet_sink = ucla.ieee802_15_4_packet_sink(self._rcvd_pktq, threshold)
        
        fg.connect(self.ieee802_15_4_demod, self._packet_sink)
        filesink = gr.file_sink (gr.sizeof_float, "/tmp/rx.log")
        fg.connect(self.ieee802_15_4_demod,filesink)
      
        gr.hier_block.__init__(self, fg, self.ieee802_15_4_demod, None)
        self._watcher = _queue_watcher_thread(self._rcvd_pktq, callback)

    def carrier_sensed(self):
        """
        Return True if we detect carrier.
        """
        return self._packet_sink.carrier_sensed()


class _queue_watcher_thread(_threading.Thread):
    def __init__(self, rcvd_pktq, callback):
        _threading.Thread.__init__(self)
        self.setDaemon(1)
        self.rcvd_pktq = rcvd_pktq
        self.callback = callback
        self.keep_running = True
        self.start()

    #def stop(self):
    #    self.keep_running = False
        
    def run(self):
        while self.keep_running:
            print "802_15_4_pkt: waiting for packet"
            msg = self.rcvd_pktq.delete_head()
            ok = 1
            payload = msg.to_string()
            
            print "received packet "
            #am_group = ord(payload[0])
            #module_src = ord(payload[1])
            #module_dst = ord(payload[2])
            #dst_addr = ord(payload[4])*256 + ord(payload[3])
            #src_addr = ord(payload[6])*256 + ord(payload[5])
            #msg_type = ord(payload[7])
            #msg_len = ord(payload[8])
            #msg_payload = payload[9:9+msg_len]
            #crc = ord(payload[-1])

            #print " bare msg: " + str(map(hex, map(ord, payload)))
            #print " am group: " + str(am_group)
            #print "  src_addr: "+str(src_addr)+" dst_addr: "+str(dst_addr)
            #print "  src_module: " + str(module_src) + " dst_module: " + str(module_dst)
            #print "  msg type: " + str(msg_type) + " msg len: " +str(msg_len)
            #print "  msg: " + str(map(hex, map(ord, msg_payload)))
            #print "  crc: " + str(crc)
            #print

            msg_payload = payload
            
            if self.callback:
                self.callback(ok, msg_payload)

