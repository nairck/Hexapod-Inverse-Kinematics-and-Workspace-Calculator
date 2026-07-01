/*
 * Academic License - for use in teaching, academic research, and meeting
 * course requirements at degree granting institutions only.  Not for
 * government, commercial, or other organizational use.
 *
 * stew_inverse_ws.h
 *
 * Code generation for function 'stew_inverse_ws'
 *
 */

#pragma once

/* Include files */
#include "rtwtypes.h"
#include "emlrt.h"
#include "mex.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Function Declarations */
void stew_inverse_ws(const emlrtStack *sp, const real_T xsi[6],
                     const real_T ysi[6], const real_T xmi[6],
                     const real_T ymi[6], real_T roll, real_T pitch, real_T yaw,
                     real_T px, real_T py, real_T pz, real_T baseZ,
                     real_T platformZ, real_T Legs[6]);

/* End of code generation (stew_inverse_ws.h) */
