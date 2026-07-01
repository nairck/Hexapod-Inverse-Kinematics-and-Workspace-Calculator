/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * stew_inverse_ws.c
 *
 * Code generation for function 'stew_inverse_ws'
 *
 */

/* Include files */
#include "stew_inverse_ws.h"
#include "rt_nonfinite.h"
#include "mwmathutil.h"

/* Variable Definitions */
static emlrtRSInfo emlrtRSI = {
    24,                /* lineNo */
    "stew_inverse_ws", /* fcnName */
    "C:\\Users\\adamb\\OneDrive\\UVic PhD Research\\SPIDERS - Mech Interface "
    "Work\\6-6 Stewart Platform\\SPIDERS Input Focus Calculator\\SPID"
    "ERS Calculator Aug 2023\\stew_inverse_ws.m" /* pathName */
};

static emlrtRTEInfo emlrtRTEI = {
    13,     /* lineNo */
    9,      /* colNo */
    "sqrt", /* fName */
    "C:\\Program "
    "Files\\MATLAB\\R2022a\\toolbox\\eml\\lib\\matlab\\elfun\\sqrt.m" /* pName
                                                                       */
};

/* Function Definitions */
void stew_inverse_ws(const emlrtStack *sp, const real_T xsi[6],
                     const real_T ysi[6], const real_T xmi[6],
                     const real_T ymi[6], real_T roll, real_T pitch, real_T yaw,
                     real_T px, real_T py, real_T pz, real_T baseZ,
                     real_T platformZ, real_T Legs[6])
{
  emlrtStack st;
  real_T b_T[18];
  real_T b_xmi[18];
  real_T diff[18];
  real_T T[12];
  real_T TXrad;
  real_T TYrad;
  real_T TZrad;
  real_T cTX;
  real_T cTY;
  real_T sTX;
  int32_T k;
  int32_T xj;
  int32_T xoffset;
  boolean_T p;
  st.prev = sp;
  st.tls = sp->tls;
  /*  Optimized inverse kinematics function for Stewart platform - put at */
  /*  beggining of code  codegen stew_inverse_ws -args {zeros(6,1), zeros(6,1),
   * zeros(6,1), zeros(6,1), 0, 0, 0, 0, 0, 0, 0, 0} */
  /*  Precompute sin/cos */
  TXrad = roll * 3.1415926535897931 / 180.0;
  TYrad = pitch * 3.1415926535897931 / 180.0;
  TZrad = yaw * 3.1415926535897931 / 180.0;
  cTX = muDoubleScalarCos(TXrad);
  sTX = muDoubleScalarSin(TXrad);
  cTY = muDoubleScalarCos(TYrad);
  TXrad = muDoubleScalarSin(TYrad);
  TYrad = muDoubleScalarCos(TZrad);
  TZrad = muDoubleScalarSin(TZrad);
  /*  Transformation matrix (only top 3 rows needed) */
  T[0] = cTY * TYrad;
  T[3] = -cTY * TZrad;
  T[6] = TXrad;
  T[9] = px;
  T[1] = sTX * TXrad * TYrad + cTX * TZrad;
  T[4] = -sTX * TXrad * TZrad + cTX * TYrad;
  T[7] = -sTX * cTY;
  T[10] = py;
  T[2] = -cTX * TXrad * TYrad + sTX * TZrad;
  T[5] = cTX * TXrad * TZrad + sTX * TYrad;
  T[8] = cTX * cTY;
  T[11] = pz;
  /*  Base points (6x3) [x, y, z] */
  /*  Platform points (6x3) [x, y, z] */
  /*  Apply transformation */
  /*  Compute leg lengths */
  for (k = 0; k < 6; k++) {
    b_xmi[3 * k] = xmi[k];
    b_xmi[3 * k + 1] = ymi[k];
    b_xmi[3 * k + 2] = platformZ;
  }
  for (k = 0; k < 3; k++) {
    TXrad = T[k];
    TYrad = T[k + 3];
    TZrad = T[k + 6];
    for (xj = 0; xj < 6; xj++) {
      b_T[k + 3 * xj] = (TXrad * b_xmi[3 * xj] + TYrad * b_xmi[3 * xj + 1]) +
                        TZrad * b_xmi[3 * xj + 2];
    }
  }
  for (k = 0; k < 6; k++) {
    b_xmi[k] = xsi[k];
    b_xmi[k + 6] = ysi[k];
    b_xmi[k + 12] = baseZ;
  }
  for (k = 0; k < 3; k++) {
    for (xj = 0; xj < 6; xj++) {
      xoffset = xj + 6 * k;
      diff[xoffset] = b_xmi[xoffset] - (b_T[k + 3 * xj] + T[k + 9]);
    }
  }
  for (k = 0; k < 18; k++) {
    TXrad = diff[k];
    b_xmi[k] = TXrad * TXrad;
  }
  for (xj = 0; xj < 6; xj++) {
    Legs[xj] = b_xmi[xj];
  }
  for (k = 0; k < 2; k++) {
    xoffset = (k + 1) * 6;
    for (xj = 0; xj < 6; xj++) {
      Legs[xj] += b_xmi[xoffset + xj];
    }
  }
  st.site = &emlrtRSI;
  p = false;
  for (k = 0; k < 6; k++) {
    if (p || (Legs[k] < 0.0)) {
      p = true;
    }
  }
  if (p) {
    emlrtErrorWithMessageIdR2018a(
        &st, &emlrtRTEI, "Coder:toolbox:ElFunDomainError",
        "Coder:toolbox:ElFunDomainError", 3, 4, 4, "sqrt");
  }
  for (k = 0; k < 6; k++) {
    Legs[k] = muDoubleScalarSqrt(Legs[k]);
  }
}

/* End of code generation (stew_inverse_ws.c) */
