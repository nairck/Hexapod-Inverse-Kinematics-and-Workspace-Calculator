/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * stew_inverse_ws_initialize.c
 *
 * Code generation for function 'stew_inverse_ws_initialize'
 *
 */

/* Include files */
#include "stew_inverse_ws_initialize.h"
#include "_coder_stew_inverse_ws_mex.h"
#include "rt_nonfinite.h"
#include "stew_inverse_ws_data.h"

/* Function Definitions */
void stew_inverse_ws_initialize(void)
{
  static const volatile char_T *emlrtBreakCheckR2012bFlagVar = NULL;
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  mex_InitInfAndNan();
  mexFunctionCreateRootTLS();
  emlrtBreakCheckR2012bFlagVar = emlrtGetBreakCheckFlagAddressR2012b();
  st.tls = emlrtRootTLSGlobal;
  emlrtClearAllocCountR2012b(&st, false, 0U, NULL);
  emlrtEnterRtStackR2012b(&st);
  emlrtFirstTimeR2012b(emlrtRootTLSGlobal);
}

/* End of code generation (stew_inverse_ws_initialize.c) */
