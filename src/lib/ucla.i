/* -*- c++ -*- */

%feature("autodoc", "1");		// generate python docstrings

%include "exception.i"
%import "gnuradio.i"			// the common stuff

%{
#include "gnuradio_swig_bug_workaround.h"	// mandatory bug fix
#include "ucla_cc1k_correlator_cb.h"
#include "ucla_sos_packet_sink.h"
#include "ucla_ieee802_15_4_packet_sink.h"
#include "ucla_delay_cc.h"
#include <stdexcept>
%}

// ----------------------------------------------------------------

/*
 * First arg is the package prefix.
 * Second arg is the name of the class minus the prefix.
 *
 * This does some behind-the-scenes magic so we can
 * access ucla_cc1k_correlator_cb from python as ucla.cc1k_correlator_cb
 */
GR_SWIG_BLOCK_MAGIC(ucla,cc1k_correlator_cb);

ucla_cc1k_correlator_cb_sptr ucla_make_cc1k_correlator_cb (int payload_bytesize,
						  unsigned char sync_byte, 
						  unsigned char nsync_byte,
						  unsigned char manchester);

class ucla_cc1k_correlator_cb : public gr_block
{
private:
  ucla_cc1k_correlator_cb ();
};

// ----------------------------------------------------------------

GR_SWIG_BLOCK_MAGIC(ucla,sos_packet_sink);

ucla_sos_packet_sink_sptr ucla_make_sos_packet_sink (const std::vector<unsigned char>& sync_vector,
						     gr_msg_queue_sptr target_queue, 
						     int threshold);

class ucla_sos_packet_sink : public gr_sync_block
{
private:
  ucla_cc1k_packet_sink ();
};


GR_SWIG_BLOCK_MAGIC(ucla,ieee802_15_4_packet_sink);

ucla_ieee802_15_4_packet_sink_sptr ucla_make_ieee802_15_4_packet_sink (gr_msg_queue_sptr target_queue, 
							   int threshold);

class ucla_ieee802_15_4_packet_sink : public gr_sync_block
{
private:
  ucla_ieee802_15_4_packet_sink ();
};


GR_SWIG_BLOCK_MAGIC(ucla,delay_cc);

ucla_delay_cc_sptr ucla_make_delay_cc (const int delay);

class ucla_delay_cc : public gr_sync_block
{
private:
  ucla_delay_cc ();
};
