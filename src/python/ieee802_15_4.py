#!/usr/bin/env python

# O-QPSK modulation and demodulation.  
#
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

# Derived from gmsk.py
#
# Modified by: Thomas Schmid
#

from gnuradio import gr, ucla
from math import pi

class ieee802_15_4_mod(gr.hier_block):

    def __init__(self, fg, spb = 2, bt = 0.3):
        """
	Hierarchical block for cc1k FSK modulation.

	The input is a byte stream (unsigned char) and the
	output is the complex modulated signal at baseband.

	@param fg: flow graph
	@type fg: flow graph
	@param spb: samples per baud >= 2
	@type spb: integer
	@param bt: Gaussian filter bandwidth * symbol time
	@type bt: float
	"""
        if not isinstance(spb, int) or spb < 2:
            raise TypeError, "sbp must be an integer >= 2"
        self.spb = spb

	sensitivity = (pi / 2) / spb	# phase change per bit = pi / 2

	# Turn it into NRZ data.
	self.nrz = gr.bytes_to_syms()

	# FM modulation
	self.fmmod = gr.frequency_modulator_fc(sensitivity)
		
	# Connect
	fg.connect(self.nrz, self.fmmod)

	# Initialize base class
	gr.hier_block.__init__(self, fg, self.nrz, self.fmmod)


class ieee802_15_4_demod(gr.hier_block):
    def __init__(self, fg, sps = 2, symbol_rate = 2000000):
        """
        Hierarchical block for O-QPSK demodulation.
        
        The input is the complex modulated signal at baseband
        and the output is a stream of bytes.
        
        @param fg: flow graph
        @type fg: flow graph
        @param sps: samples per symbol
        @type sps: integer
        @param symbol_rate: symbols per second
        @type symbol_rate: float
        """
        
        # Demodulate FM
        sensitivity = (pi / 2) / sps
        #self.fmdemod = gr.quadrature_demod_cf(1.0 / sensitivity)
        self.fmdemod = gr.quadrature_demod_cf(1)
        
        # Low pass the output of fmdemod to allow us to remove
        # the DC offset resulting from frequency offset
        
        alpha = 0.0008/sps
        self.freq_offset = gr.single_pole_iir_filter_ff(alpha)
        self.sub = gr.sub_ff()
        
        fg.connect(self.fmdemod, (self.sub, 0))
        fg.connect(self.fmdemod, self.freq_offset, (self.sub, 1))
        
        
        # recover the clock
        omega = sps
        gain_mu=0.03
        mu=0.5
        omega_relative_limit=0.0002
        freq_error=0.0
        
        gain_omega = .25*gain_mu*gain_mu        # critically damped
        self.clock_recovery = gr.clock_recovery_mm_ff(omega, gain_omega, mu, gain_mu,
                                                      omega_relative_limit)
        
        # Connect
        fg.connect(self.sub, self.clock_recovery)
        
        # Initialize base class
        gr.hier_block.__init__(self, fg, self.fmdemod, self.clock_recovery)
        
# vim:ts=8
