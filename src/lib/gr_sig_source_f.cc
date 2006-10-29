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
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

// WARNING: this file is machine generated.  Edits will be over written

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif
#include <gr_sig_source_f.h>
#include <algorithm>
#include <gr_io_signature.h>
#include <stdexcept>
#include <gr_complex.h>


gr_sig_source_f::gr_sig_source_f (double sampling_freq, gr_waveform_t waveform,
		double frequency, double ampl, float offset)
  : gr_sync_block ("sig_source_f",
		   gr_make_io_signature (0, 0, 0),
		   gr_make_io_signature (1, 1, sizeof (float))),
    d_sampling_freq (sampling_freq), d_waveform (waveform), d_frequency (frequency),
    d_ampl (ampl), d_offset (offset)
{
  d_nco.set_freq (2 * M_PI * d_frequency / d_sampling_freq);
}

gr_sig_source_f_sptr
gr_make_sig_source_f (double sampling_freq, gr_waveform_t waveform,
		     double frequency, double ampl, float offset)
{
  return gr_sig_source_f_sptr (new gr_sig_source_f (sampling_freq, waveform, frequency, ampl, offset));
}

int
gr_sig_source_f::work (int noutput_items,
		    gr_vector_const_void_star &input_items,
		    gr_vector_void_star &output_items)
{
  float *optr = (float *) output_items[0];
  float t;

  switch (d_waveform){

#if 0	// complex?

  case GR_CONST_WAVE:
    t = (gr_complex) d_ampl + d_offset;
    for (int i = 0; i < noutput_items; i++)	// FIXME unroll
      optr[i] = t;
    break;
    
  case GR_SIN_WAVE:
  case GR_COS_WAVE:
    d_nco.sincos (optr, noutput_items, d_ampl);
    if (d_offset == gr_complex(0,0))
      break;

    for (int i = 0; i < noutput_items; i++){
      optr[i] += d_offset;
    }
    break;

#else			// nope...

  case GR_CONST_WAVE:
    t = (float) d_ampl + d_offset;
    for (int i = 0; i < noutput_items; i++)	// FIXME unroll
      optr[i] = t;
    break;
    
  case GR_SIN_WAVE:
    d_nco.sin (optr, noutput_items, d_ampl);
    if (d_offset == 0)
      break;

    for (int i = 0; i < noutput_items; i++){
      optr[i] += d_offset;
    }
    break;

  case GR_COS_WAVE:
    d_nco.cos (optr, noutput_items, d_ampl);
    if (d_offset == 0)
      break;

    for (int i = 0; i < noutput_items; i++){
      optr[i] += d_offset;
    }
    break;
#endif

  default:
    throw std::runtime_error ("gr_sig_source: invalid waveform");
  }

  return noutput_items;
}

void
gr_sig_source_f::set_sampling_freq (double sampling_freq)
{
  d_sampling_freq = sampling_freq;
  d_nco.set_freq (2 * M_PI * d_frequency / d_sampling_freq);
}

void
gr_sig_source_f::set_waveform (gr_waveform_t waveform)
{
  d_waveform = waveform;
}

void
gr_sig_source_f::set_frequency (double frequency)
{
  d_frequency = frequency;
  d_nco.set_freq (2 * M_PI * d_frequency / d_sampling_freq);
}

void
gr_sig_source_f::set_amplitude (double ampl)
{
  d_ampl = ampl;
}

void
gr_sig_source_f::set_offset (float offset)
{
  d_offset = offset;
}

