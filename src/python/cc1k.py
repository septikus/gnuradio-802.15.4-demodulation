#!/usr/bin/env python

# GMSK modulation and demodulation.  
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

class cc1k_mod(gr.hier_block):

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


class cc1k_demod(gr.hier_block):
	def __init__(self, fg, sps = 8, symbol_rate = 38400, p_size = 13):
		"""
		Hierarchical block for FSK demodulation.

		The input is the complex modulated signal at baseband
		and the output is a stream of bytes.

		@param fg: flow graph
		@type fg: flow graph
		@param sps: samples per symbol
		@type sps: integer
		@param symbol_rate: symbols per second
		@type symbol_rate: float
		@param p_size: packet size
		@type p_size: integer
		"""
		
		# Demodulate FM
		sensitivity = (pi / 2) / sps
		#self.fmdemod = gr.quadrature_demod_cf(1.0 / sensitivity)
		self.fmdemod = gr.quadrature_demod_cf(1)

		# Integrate over a bit length to smooth noise
		#integrate_taps = (1.0 / sps,) * sps
		#integrate_taps = (1.0,0,0,0,0,0,0,0,0)
		#self.integrate_filter = gr.fir_filter_fff(1, integrate_taps)

		# Bit slice, try and find the center of the bit from the sync
		# field placed by the framer, output p_size bytes at a time.
		self.correlator = ucla.cc1k_correlator_cb(p_size, 0, 0, 0)

		# Connect
                fg.connect(self.fmdemod, self.correlator)

		# Initialize base class
		gr.hier_block.__init__(self, fg, self.fmdemod, self.correlator)

# vim:ts=8