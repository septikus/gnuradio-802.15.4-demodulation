
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <ucla_qpsk_modulator_fc.h>
#include <gr_io_signature.h>
#include <assert.h>

static const int SAMPLES_PER_SYMBOL = 2;

ucla_qpsk_modulator_fc_sptr 
ucla_make_qpsk_modulator_fc ()
{
  return ucla_qpsk_modulator_fc_sptr (new ucla_qpsk_modulator_fc ());
}

ucla_qpsk_modulator_fc::ucla_qpsk_modulator_fc ()
  : gr_sync_interpolator ("qpsk_modulator_fc",
			  gr_make_io_signature (1, 1, sizeof (float)),
			  gr_make_io_signature (1, 1, sizeof (gr_complex)),
			  SAMPLES_PER_SYMBOL)
{
}

ucla_qpsk_modulator_fc::~ucla_qpsk_modulator_fc()
{
  return;
}

int
ucla_qpsk_modulator_fc::work (int noutput_items,
			gr_vector_const_void_star &input_items,
			gr_vector_void_star &output_items)
{
  const float *in = (float *) input_items[0];
  gr_complex *out = (gr_complex *) output_items[0];

  assert (noutput_items % SAMPLES_PER_SYMBOL == 0);

  for (int i = 0; i < noutput_items / SAMPLES_PER_SYMBOL / 2; i++){
    float iphase = in[2*i];
    float qphase = in[2*i+1];

    *out++ = gr_complex(0.0, 0.0);
    *out++ = gr_complex(iphase * 0.70710678, qphase * 0.70710678);
    *out++ = gr_complex(iphase, qphase);
    *out++ = gr_complex(iphase * 0.70710678, qphase * 0.70710678);
  }

  return noutput_items;
}


  
