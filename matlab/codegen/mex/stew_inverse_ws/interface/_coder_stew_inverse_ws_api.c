/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * _coder_stew_inverse_ws_api.c
 *
 * Code generation for function '_coder_stew_inverse_ws_api'
 *
 */

/* Include files */
#include "_coder_stew_inverse_ws_api.h"
#include "rt_nonfinite.h"
#include "stew_inverse_ws.h"
#include "stew_inverse_ws_data.h"

/* Function Declarations */
static real_T (*b_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                                   const emlrtMsgIdentifier *parentId))[6];

static real_T c_emlrt_marshallIn(const emlrtStack *sp, const mxArray *roll,
                                 const char_T *identifier);

static real_T d_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                                 const emlrtMsgIdentifier *parentId);

static real_T (*e_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                                   const emlrtMsgIdentifier *msgId))[6];

static real_T (*emlrt_marshallIn(const emlrtStack *sp, const mxArray *xsi,
                                 const char_T *identifier))[6];

static const mxArray *emlrt_marshallOut(const real_T u[6]);

static real_T f_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                                 const emlrtMsgIdentifier *msgId);

/* Function Definitions */
static real_T (*b_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                                   const emlrtMsgIdentifier *parentId))[6]
{
  real_T(*y)[6];
  y = e_emlrt_marshallIn(sp, emlrtAlias(u), parentId);
  emlrtDestroyArray(&u);
  return y;
}

static real_T c_emlrt_marshallIn(const emlrtStack *sp, const mxArray *roll,
                                 const char_T *identifier)
{
  emlrtMsgIdentifier thisId;
  real_T y;
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  y = d_emlrt_marshallIn(sp, emlrtAlias(roll), &thisId);
  emlrtDestroyArray(&roll);
  return y;
}

static real_T d_emlrt_marshallIn(const emlrtStack *sp, const mxArray *u,
                                 const emlrtMsgIdentifier *parentId)
{
  real_T y;
  y = f_emlrt_marshallIn(sp, emlrtAlias(u), parentId);
  emlrtDestroyArray(&u);
  return y;
}

static real_T (*e_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                                   const emlrtMsgIdentifier *msgId))[6]
{
  static const int32_T dims = 6;
  real_T(*ret)[6];
  emlrtCheckBuiltInR2012b((emlrtCTX)sp, msgId, src, (const char_T *)"double",
                          false, 1U, (void *)&dims);
  ret = (real_T(*)[6])emlrtMxGetData(src);
  emlrtDestroyArray(&src);
  return ret;
}

static real_T (*emlrt_marshallIn(const emlrtStack *sp, const mxArray *xsi,
                                 const char_T *identifier))[6]
{
  emlrtMsgIdentifier thisId;
  real_T(*y)[6];
  thisId.fIdentifier = (const char_T *)identifier;
  thisId.fParent = NULL;
  thisId.bParentIsCell = false;
  y = b_emlrt_marshallIn(sp, emlrtAlias(xsi), &thisId);
  emlrtDestroyArray(&xsi);
  return y;
}

static const mxArray *emlrt_marshallOut(const real_T u[6])
{
  static const int32_T i = 0;
  static const int32_T i1 = 6;
  const mxArray *m;
  const mxArray *y;
  y = NULL;
  m = emlrtCreateNumericArray(1, (const void *)&i, mxDOUBLE_CLASS, mxREAL);
  emlrtMxSetData((mxArray *)m, (void *)&u[0]);
  emlrtSetDimensions((mxArray *)m, &i1, 1);
  emlrtAssign(&y, m);
  return y;
}

static real_T f_emlrt_marshallIn(const emlrtStack *sp, const mxArray *src,
                                 const emlrtMsgIdentifier *msgId)
{
  static const int32_T dims = 0;
  real_T ret;
  emlrtCheckBuiltInR2012b((emlrtCTX)sp, msgId, src, (const char_T *)"double",
                          false, 0U, (void *)&dims);
  ret = *(real_T *)emlrtMxGetData(src);
  emlrtDestroyArray(&src);
  return ret;
}

void stew_inverse_ws_api(const mxArray *const prhs[12], const mxArray **plhs)
{
  emlrtStack st = {
      NULL, /* site */
      NULL, /* tls */
      NULL  /* prev */
  };
  real_T(*Legs)[6];
  real_T(*xmi)[6];
  real_T(*xsi)[6];
  real_T(*ymi)[6];
  real_T(*ysi)[6];
  real_T baseZ;
  real_T pitch;
  real_T platformZ;
  real_T px;
  real_T py;
  real_T pz;
  real_T roll;
  real_T yaw;
  st.tls = emlrtRootTLSGlobal;
  Legs = (real_T(*)[6])mxMalloc(sizeof(real_T[6]));
  /* Marshall function inputs */
  xsi = emlrt_marshallIn(&st, emlrtAlias(prhs[0]), "xsi");
  ysi = emlrt_marshallIn(&st, emlrtAlias(prhs[1]), "ysi");
  xmi = emlrt_marshallIn(&st, emlrtAlias(prhs[2]), "xmi");
  ymi = emlrt_marshallIn(&st, emlrtAlias(prhs[3]), "ymi");
  roll = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[4]), "roll");
  pitch = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[5]), "pitch");
  yaw = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[6]), "yaw");
  px = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[7]), "px");
  py = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[8]), "py");
  pz = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[9]), "pz");
  baseZ = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[10]), "baseZ");
  platformZ = c_emlrt_marshallIn(&st, emlrtAliasP(prhs[11]), "platformZ");
  /* Invoke the target function */
  stew_inverse_ws(&st, *xsi, *ysi, *xmi, *ymi, roll, pitch, yaw, px, py, pz,
                  baseZ, platformZ, *Legs);
  /* Marshall function outputs */
  *plhs = emlrt_marshallOut(*Legs);
}

/* End of code generation (_coder_stew_inverse_ws_api.c) */
