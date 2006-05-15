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

/*
 * ucla_ieee802_15_4_packet_sink.cc has been derived from gr_packet_sink.cc
 *
 * Modified by: Thomas Schmid
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <ucla_ieee802_15_4_packet_sink.h>
#include <gr_io_signature.h>
#include <cstdio>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdexcept>
#include <gr_count_bits.h>

#define VERBOSE 0

static const int DEFAULT_THRESHOLD = 0;  // detect access code with up to DEFAULT_THRESHOLD bits wrong
  // this is the mapping between chips and symbols if we do
  // a fm demodulation of the O-QPSK signal. Note that this
  // is different than the O-QPSK chip sequence from the
  // 802.15.4 standard since there there is a translation
  // happening.
  // See "CMOS RFIC Architectures for IEEE 802.15.4 Networks",
  // John Notor, Anthony Caviglia, Gary Levy, for more details.
static const int CHIP_MAPPING[] = {1618456172,
				   1309113062,
				   1826650030,
				   1724778362,
				   778887287,
				   2061946375,
				   2007919840,
				   125494990,
				   529027475,
				   838370585,
				   320833617,
				   422705285,
				   1368596360,
				   85537272,
				   139563807,
				   2021988657};


inline void
ucla_ieee802_15_4_packet_sink::enter_search()
{
  if (VERBOSE)
    fprintf(stderr, "@ enter_search\n");

  d_state = STATE_SYNC_SEARCH;
  d_shift_reg = 0;
  d_preamble_cnt = 0;
  d_chip_cnt = 0;
  d_packet_byte = 0;
}
    
inline void
ucla_ieee802_15_4_packet_sink::enter_have_sync()
{
  if (VERBOSE)
    fprintf(stderr, "@ enter_have_sync\n");

  d_state = STATE_HAVE_SYNC;
  d_packetlen_cnt = 0;
  d_packet_byte = 0;
  d_packet_byte_index = 0;
}

inline void
ucla_ieee802_15_4_packet_sink::enter_have_header(int payload_len)
{
  if (VERBOSE)
    fprintf(stderr, "@ enter_have_header (payload_len = %d)\n", payload_len);
  
  d_state = STATE_HAVE_HEADER;
  d_packetlen  = payload_len;
  d_payload_cnt = 0;
  d_packet_byte = 0;
  d_packet_byte_index = 0;
}


inline unsigned char
ucla_ieee802_15_4_packet_sink::decode_chips(unsigned int chips){
  int i;

  for(i=0; i<16; i++) {
    // FIXME: we can store the last chip
    // ignore the first chip since it depends on the last chip.
    if (gr_count_bits32((chips&0x7FFFFFFF) ^ CHIP_MAPPING[i]) <= d_threshold) {
      return (char)i&0xFF;
    }
  }
  return 0xFF;
}

ucla_ieee802_15_4_packet_sink_sptr
ucla_make_ieee802_15_4_packet_sink (gr_msg_queue_sptr target_queue, 
			   int threshold)
{
  return ucla_ieee802_15_4_packet_sink_sptr (new ucla_ieee802_15_4_packet_sink (target_queue, threshold));
}


ucla_ieee802_15_4_packet_sink::ucla_ieee802_15_4_packet_sink (gr_msg_queue_sptr target_queue, int threshold)
  : gr_sync_block ("sos_packet_sink",
		   gr_make_io_signature (1, 1, sizeof(float)),
		   gr_make_io_signature (0, 0, 0)),
    d_target_queue(target_queue), 
    d_threshold(threshold == -1 ? DEFAULT_THRESHOLD : threshold)
{
  d_sync_vector = 0xA7;

  if ( VERBOSE )
    fprintf(stderr, "syncvec: %x\n", d_sync_vector),fflush(stderr);

  enter_search();
}

ucla_ieee802_15_4_packet_sink::~ucla_ieee802_15_4_packet_sink ()
{
}

int ucla_ieee802_15_4_packet_sink::work (int noutput_items,
		      gr_vector_const_void_star &input_items,
		      gr_vector_void_star &output_items)
{
  float *inbuf = (float *) input_items[0];
  int count=0;
  
  if (VERBOSE)
    fprintf(stderr,">>> Entering state machine\n"),fflush(stderr);

  while (count<noutput_items) {
    switch(d_state) {
      
    case STATE_SYNC_SEARCH:    // Look for sync vector
      if (VERBOSE)
	fprintf(stderr,"SYNC Search, noutput=%d syncvec=%x\n",noutput_items, d_sync_vector),fflush(stderr);

      while (count < noutput_items) {

	if(slice(inbuf[count++]))
	  d_shift_reg = (d_shift_reg << 1) | 1;
	else
	  d_shift_reg = d_shift_reg << 1;

	if(d_preamble_cnt > 0){
	  d_chip_cnt = (d_chip_cnt+1)%32;
	}

	if(d_preamble_cnt == 0){
	  unsigned int threshold;
	  threshold = gr_count_bits32((d_shift_reg&0x7FFFFFFF) ^ CHIP_MAPPING[0]);
	  //if(threshold < 5)
	  //  fprintf(stderr, "Threshold %d d_preamble_cnt: %d\n", threshold, d_preamble_cnt);
	  if ( threshold <= d_threshold) {
	    if (VERBOSE)
	      fprintf(stderr,"Found 0 in chip sequence\n"),fflush(stderr);	
	    // we found a 0 in the chip sequence
	    d_preamble_cnt+=1;
	    //fprintf(stderr, "Threshold %d d_preamble_cnt: %d\n", threshold, d_preamble_cnt);
	  }
	} else {
	  // we found the first 0, thus we only have to do the calculation every 32 chips
	  if(d_chip_cnt%32 == 0){
	    if(d_preamble_cnt < 8) {
	      if (gr_count_bits32((d_shift_reg&0x7FFFFFFF) ^ CHIP_MAPPING[0]) <= d_threshold) {
		if (VERBOSE)
		  fprintf(stderr,"Found 0 in chip sequence\n"),fflush(stderr);	
		// we found a 0 in the chip sequence
		d_preamble_cnt ++;
	      } else {
		if (VERBOSE)
		  fprintf(stderr,"No 0, reset counter. %u\n", d_shift_reg),fflush(stderr);	
		
		// no 0, restart search
		enter_search();
		break;
	      }
	    } else {
	      // we found 8 zeros in the chip sequences check if we have the SFD
	      if(d_packet_byte == 0) {
		if (gr_count_bits32((d_shift_reg&0x7FFFFFFF) ^ CHIP_MAPPING[7]) <= d_threshold) {
		  d_packet_byte = 7<<4;
		} else {
		  // we are not in the synchronization header
		  if (VERBOSE)
		    fprintf(stderr, "Wrong first byte of SFD. %u\n", d_shift_reg), fflush(stderr);
		  enter_search();
		  break;
		}
	      } else {
		if (gr_count_bits32((d_shift_reg&0x7FFFFFFF) ^ CHIP_MAPPING[10]) <= d_threshold) {
		  if (VERBOSE)
		    fprintf(stderr,"Found sync\n"),fflush(stderr);	
		  // found SDF
		  d_packet_byte = 0xA<<4;
		  // setup for header decode
		  enter_have_sync();
		  break;
		} else {
		  if (VERBOSE)
		    fprintf(stderr, "Wrong second byte of SFD. %u\n", d_shift_reg), fflush(stderr);
		  enter_search();
		  break;
		}
	      }
	    } 
	  }
	}
      }
      break;

    case STATE_HAVE_SYNC:
      if (VERBOSE)
	fprintf(stderr,"Header Search bitcnt=%d, header=0x%08x\n", d_headerbitlen_cnt, d_header),
	  fflush(stderr);

      while (count < noutput_items) {		// Decode the bytes one after another.
	if(slice(inbuf[count++]))
	  d_shift_reg = (d_shift_reg << 1) | 1;
	else
	  d_shift_reg = d_shift_reg << 1;

	d_chip_cnt = (d_chip_cnt+1)%32;

	if(d_chip_cnt == 0){
	  unsigned char c = decode_chips(d_shift_reg);
	  if(c == 0xFF){
	    // something is wrong. restart the search for a sync
	    if(VERBOSE)
	      fprintf(stderr, "Found a not valid chip sequence! %u\n", d_shift_reg), fflush(stderr);
	      
	    enter_search();
	    break;
	  }

	  if(d_packet_byte_index == 0){
	    d_packet_byte = c;
	  } else {
	    // c is always < 15
	    d_packet_byte |= c << 4;
	  }
	  d_packet_byte_index = d_packet_byte_index + 1;
	  if(d_packet_byte_index%2 == 0){
	    // we have a complete byte which represents the frame length.
	    int frame_len = d_packet_byte;
	    if(frame_len <= MAX_PKT_LEN){
	      enter_have_header(frame_len);
	    } else {
	      enter_search();
	    }
	    break;
	  }
	}
      }
      break;
      
    case STATE_HAVE_HEADER:
      if (VERBOSE)
	fprintf(stderr,"Packet Build count=%d, noutput_items=%d\n", count, noutput_items),fflush(stderr);

      while (count < noutput_items) {   // shift bits into bytes of packet one at a time
	if(slice(inbuf[count++]))
	  d_shift_reg = (d_shift_reg << 1) | 1;
	else
	  d_shift_reg = d_shift_reg << 1;

	d_chip_cnt = (d_chip_cnt+1)%32;

	if(d_chip_cnt == 0){
	  unsigned char c = decode_chips(d_shift_reg);
	  if(c == 0xff){
	    // something is wrong. restart the search for a sync
	    if(VERBOSE)
	      fprintf(stderr, "Found a not valid chip sequence! %u\n", d_shift_reg), fflush(stderr);

	    enter_search();
	    break;
	  }
	  // the first symbol represents the first part of the byte.
	  if(d_packet_byte_index == 0){
	    d_packet_byte = c;
	  } else {
	    // c is always < 15
	    d_packet_byte |= c << 4;
	  }
	  //fprintf(stderr, "%d: 0x%x\n", d_packet_byte_index, c);
	  d_packet_byte_index = d_packet_byte_index + 1;
	  if(d_packet_byte_index%2 == 0){
	    // we have a complete byte
	    if (VERBOSE)
	      fprintf(stderr, "packetcnt: %d, payloadcnt: %d, payload 0x%x, d_packet_byte_index: %d\n", d_packetlen_cnt, d_payload_cnt, d_packet_byte, d_packet_byte_index), fflush(stderr);

	    d_packet[d_packetlen_cnt++] = d_packet_byte;
	    d_payload_cnt++;
	    d_packet_byte_index = 0;

	    if (d_payload_cnt >= d_packetlen){	// packet is filled, including CRC. might do check later in here

	      // build a message
	      gr_message_sptr msg = gr_make_message(0, 0, 0, d_packetlen_cnt);  	    
	      memcpy(msg->msg(), d_packet, d_packetlen_cnt);

	      d_target_queue->insert_tail(msg);		// send it
	      msg.reset();  				// free it up
	      if(VERBOSE)
		fprintf(stderr, "Adding message of size %d to queue\n", d_packetlen_cnt);
	      enter_search();
	      break;
	    }
	  }
	}
      }
      break;

    default:
      assert(0);

    } // switch

  }   // while

  return noutput_items;
}
  
