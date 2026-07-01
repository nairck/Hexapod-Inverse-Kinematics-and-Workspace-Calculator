function Legs = stew_inverse_ws(xsi, ysi, xmi, ymi, roll, pitch, yaw, px, py, pz, baseZ, platformZ)
%#codegen
% Optimized inverse kinematics function for a hexapod - put at
% CALL THIS ONCE TO COMPILE MEX FILE AND CODEGEN FOLDER FROM SCRATCH:
%       codegen stew_inverse_ws -args {zeros(6,1), zeros(6,1), zeros(6,1), zeros(6,1), 0, 0, 0, 0, 0, 0, 0, 0}
% Precompute sin/cos
TXrad = roll * pi/180;
TYrad = pitch * pi/180;
TZrad = yaw * pi/180;
cTX = cos(TXrad); sTX = sin(TXrad);
cTY = cos(TYrad); sTY = sin(TYrad);
cTZ = cos(TZrad); sTZ = sin(TZrad);
% Transformation matrix (only top 3 rows needed)
T = [cTY*cTZ,            -cTY*sTZ,           sTY,  px;
     sTX*sTY*cTZ+cTX*sTZ, -sTX*sTY*sTZ+cTX*cTZ, -sTX*cTY, py;
    -cTX*sTY*cTZ+sTX*sTZ,  cTX*sTY*sTZ+sTX*cTZ,  cTX*cTY, pz];
% Base points (6x3) [x, y, z]
a = [xsi(:), ysi(:), baseZ*ones(6,1)];
% Platform points (6x3) [x, y, z]
b = [xmi(:), ymi(:), platformZ*ones(6,1)];
% Apply transformation
b_trans = (T(1:3,1:3) * b.' + T(1:3,4)).';
% Compute leg lengths
diff = a - b_trans;
Legs = sqrt(sum(diff.^2, 2));
