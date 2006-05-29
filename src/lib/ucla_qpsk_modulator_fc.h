/* -*- c++ -*- */

#ifndef INCLUDED_UCLA_QPSK_MODULATOR_FC_H
#define INCLUDED_UCLA_QPSK_MODULATOR_FC_H

#include <gr_sync_interpolator.h>
#include <gr_types.h>
#include <gr_io_signature.h>

class ucla_qpsk_modulator_fc;

typedef boost::shared_ptr<ucla_qpsk_modulator_fc> ucla_qpsk_modulator_fc_sptr;

ucla_qpsk_modulator_fc_sptr 
ucla_make_qpsk_modulator_fc ();

/*!
 * \brief 
 * \ingroup block
 *
 * input: 
 *
 */

class ucla_qpsk_modulator_fc : public gr_sync_interpolator
{
  friend ucla_qpsk_modulator_fc_sptr ucla_make_qpsk_modulator_fc ();

 protected:
  ucla_qpsk_modulator_fc ();

 public:
  ~ucla_qpsk_modulator_fc();


  int work (int noutput_items,
	    gr_vector_const_void_star &input_items,
	    gr_vector_void_star &output_items);

};

#endif /* INCLUDED_UCLA_QPSK_MODULATOR_FC_H */
