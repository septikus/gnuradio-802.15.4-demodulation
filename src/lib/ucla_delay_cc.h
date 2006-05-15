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

#ifndef INCLUDED_UCLA_DELAY_CC_H
#define INCLUDED_UCLA_DELAY_CC_H

#include <gr_sync_block.h>
#include <gr_io_signature.h>
#include <gr_types.h>

class ucla_delay_cc;
typedef boost::shared_ptr<ucla_delay_cc> ucla_delay_cc_sptr;

// public constructor
ucla_delay_cc_sptr ucla_make_delay_cc (const int delay);

/*!
 * \brief Filter-Delay Combination Block.
 * \ingroup filter
 *
 * The block takes one or two float stream and outputs a complex
 * stream. If only one float stream is input, the real output is
 * a delayed version of this input and the imaginary output is the
 * filtered output. If two floats are connected to the input, then
 * the real output is the delayed version of the first input, and
 * the imaginary output is the filtered output. The delay in the 
 * real path accounts for the group delay introduced by the filter
 * in the imaginary path. The filter taps needs to be calculated
 * before initializing this block.
 *
 */
class ucla_delay_cc : public gr_sync_block
{
 public:
  ~ucla_delay_cc ();

  int work (int noutput_items,
	    gr_vector_const_void_star &input_items,
	    gr_vector_void_star &output_items);

 protected:
  ucla_delay_cc (const int delay);

 private:
  unsigned int  d_delay;

  friend ucla_delay_cc_sptr ucla_make_delay_cc (const int delay);
};

#endif /* INCLUDED_UCLA_DELAY_CC_H */
