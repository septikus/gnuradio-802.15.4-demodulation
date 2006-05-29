/* -*- c++ -*- */
/*
 * Copyright 2004 Free Software Foundation, Inc.
 * 
 * This file is part of GNU Radio
 * 
 * GNU Radio is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 * 
 * GNU Radio is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with GNU Radio; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

// WARNING: this file is machine generated.  Edits will be over written

#ifndef INCLUDED_UCLA_SYMBOLS_TO_CHIPS_BI_H
#define INCLUDED_UCLA_SYMBOLS_TO_CHIPS_BI_H

#include <gr_sync_interpolator.h>

class ucla_symbols_to_chips_bi;
typedef boost::shared_ptr<ucla_symbols_to_chips_bi> ucla_symbols_to_chips_bi_sptr;

ucla_symbols_to_chips_bi_sptr ucla_make_symbols_to_chips_bi ();

/*!
 * \brief Map a stream of symbol indexes (unpacked bytes or shorts) to stream of float or complex onstellation points.in \p D dimensions (\p D = 1 by default)
 * \ingroup block
 *
 * input: stream of unsigned char; output: stream of float
 *
 * out[n D + k] = symbol_table[in[n] D + k], k=0,1,...,D-1
 *
 * The combination of gr_packed_to_unpacked_XX followed by
 * gr_chunks_to_symbols_XY handles the general case of mapping 
 * from a stream of bytes or shorts into arbitrary float
 * or complex symbols.
 *
 * \sa gr_packed_to_unpacked_bb, gr_unpacked_to_packed_bb,
 * \sa gr_packed_to_unpacked_ss, gr_unpacked_to_packed_ss,
 * \sa gr_symbols_to_chips_bi, gr_chunks_to_symbols_bc.
 * \sa gr_chunks_to_symbols_sf, gr_chunks_to_symbols_sc.
 */

class ucla_symbols_to_chips_bi : public gr_sync_interpolator
{
  friend ucla_symbols_to_chips_bi_sptr ucla_make_symbols_to_chips_bi ();

  //std::vector<long> d_symbol_table;
  ucla_symbols_to_chips_bi ();

 public:
  //std::vector<unsigned int> symbol_table () const { return d_symbol_table; }
  int work (int noutput_items,
	    gr_vector_const_void_star &input_items,
	    gr_vector_void_star &output_items);

  bool check_topology(int ninputs, int noutputs) { return ninputs == noutputs; }
};

#endif
