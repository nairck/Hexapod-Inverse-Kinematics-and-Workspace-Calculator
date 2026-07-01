/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * _coder_stew_inverse_ws_mex.c
 *
 * Code generation for function '_coder_stew_inverse_ws_mex'
 *
 */

/* Include files */
#include "_coder_stew_inverse_ws_mex.h"
#include "_coder_stew_inverse_ws_api.h"
#include "rt_nonfinite.h"
#include "stew_inverse_ws_data.h"
#include "stew_inverse_ws_initialize.h"
#include "stew_inverse_ws_terminate.h"

/* Function Definitions */
void mexFunction(int32_T nlhs, mxArray *plhs[], int32_T nrhs,
                 const mxArray *prhs[])
{
  mexAtExit(&stew_inverse_ws_atexit);
  /* Module initialization. */
  stew_inverse_ws_initialize();
  /* Dispatch the entry-point. */
  stew_inverse_ws_mexFunction(nlhs, plhs, nrhs, prhs);
  /* Module termination. */
  stew_inverse_ws_terminate();
}

emlrtCTX mexFunctionCreateRootTLS(void)
{
  emlrtCreateRootTLSR2022a(&emlrtRootTLSGlobal, &emlrtContextGlobal, NULL, 1,
                           NULL, (const char_T *)"windows-1252", true);
  return emlrtRootTLSGlobal;
}

void stew_inverse_ws_mexFunction(int32_T nlhs, mxArray *plhs[1], int32_T nrhs,
                                 const mxArray *prhs[12])
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  const mxArray *outputs;
  st.tls = emlrtRootTLSGlobal;
  /* Check for proper number of arguments. */
  if (nrhs != 12) {
    emlrtErrMsgIdAndTxt(&st, "EMLRT:runTime:WrongNumberOfInputs", 5, 12, 12, 4,
                        15, "stew_inverse_ws");
  }
  if (nlhs > 1) {
    emlrtErrMsgIdAndTxt(&st, "EMLRT:runTime:TooManyOutputArguments", 3, 4, 15,
                        "stew_inverse_ws");
  }
  /* Call the function. */
  stew_inverse_ws_api(prhs, &outputs);
  /* Copy over outputs to the caller. */
  emlrtReturnArrays(1, &plhs[0], &outputs);
}

/* End of code generation (_coder_stew_inverse_ws_mex.c) */
