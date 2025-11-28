function inv_return=stew_inverse(xsi,ysi,xmi,ymi,roll,pitch,yaw,px,py,pz,baseZ,platformZ)
%digits(15)                           %digit accuracy specification
a1=[xsi(1);ysi(1);baseZ;1];
a2=[xsi(2);ysi(2);baseZ;1];
a3=[xsi(3);ysi(3);baseZ;1];
a4=[xsi(4);ysi(4);baseZ;1];
a5=[xsi(5);ysi(5);baseZ;1];
a6=[xsi(6);ysi(6);baseZ;1];
TXrad=roll*pi/180;                  %convert the roll angle to radians
TYrad=pitch*pi/180;                 %convert the pitch angle to radians
TZrad=yaw*pi/180;                   %convert the yaw angle to radians
%T is the transformation (translation + rotation) matrix from Frame B to Frame N.
T =[cos(TYrad)*cos(TZrad),                                 -cos(TYrad)*sin(TZrad),                                  sin(TYrad),           px;
    sin(TXrad)*sin(TYrad)*cos(TZrad)+cos(TXrad)*sin(TZrad),-sin(TXrad)*sin(TYrad)*sin(TZrad)+cos(TXrad)*cos(TZrad),-sin(TXrad)*cos(TYrad),py;
    -cos(TXrad)*sin(TYrad)*cos(TZrad)+sin(TXrad)*sin(TZrad), cos(TXrad)*sin(TYrad)*sin(TZrad)+sin(TXrad)*cos(TZrad), cos(TXrad)*cos(TYrad),pz;
    0,                                                      0,                                                      0,                    1 ];
%Ta is the transformation matrix that rotates and translates the
%platform to the correct orientation for animation.
Ta =[cos(TYrad)*cos(TZrad),                                 -cos(TYrad)*sin(TZrad),                                  sin(TYrad),           px;
    sin(TXrad)*sin(TYrad)*cos(TZrad)+cos(TXrad)*sin(TZrad),-sin(TXrad)*sin(TYrad)*sin(TZrad)+cos(TXrad)*cos(TZrad),-sin(TXrad)*cos(TYrad),py;
    -cos(TXrad)*sin(TYrad)*cos(TZrad)+sin(TXrad)*sin(TZrad), cos(TXrad)*sin(TYrad)*sin(TZrad)+sin(TXrad)*cos(TZrad), cos(TXrad)*cos(TYrad),pz;
    0,                                                      0,                                                      0,                    1 ];
b1=T*[xmi(1);ymi(1);platformZ;1];   %b# is the coordinates that will be used for calculation
b2=T*[xmi(2);ymi(2);platformZ;1];
b3=T*[xmi(3);ymi(3);platformZ;1];
b4=T*[xmi(4);ymi(4);platformZ;1];
b5=T*[xmi(5);ymi(5);platformZ;1];
b6=T*[xmi(6);ymi(6);platformZ;1];
b1t=Ta*[xmi(1);ymi(1);platformZ;1]; %b#t are the coordinates that will be animated
b2t=Ta*[xmi(2);ymi(2);platformZ;1];
b3t=Ta*[xmi(3);ymi(3);platformZ;1];
b4t=Ta*[xmi(4);ymi(4);platformZ;1];
b5t=Ta*[xmi(5);ymi(5);platformZ;1];
b6t=Ta*[xmi(6);ymi(6);platformZ;1];
L1=sqrt((abs(a1(1)-b1(1)))^2+(abs(a1(2)-b1(2)))^2+(abs(a1(3)-b1(3)))^2); %L=sqrt((ax-bx)^2+(ay-by)^2+(az-bz)^2)
L2=sqrt((abs(a2(1)-b2(1)))^2+(abs(a2(2)-b2(2)))^2+(abs(a2(3)-b2(3)))^2);
L3=sqrt((abs(a3(1)-b3(1)))^2+(abs(a3(2)-b3(2)))^2+(abs(a3(3)-b3(3)))^2);
L4=sqrt((abs(a4(1)-b4(1)))^2+(abs(a4(2)-b4(2)))^2+(abs(a4(3)-b4(3)))^2);
L5=sqrt((abs(a5(1)-b5(1)))^2+(abs(a5(2)-b5(2)))^2+(abs(a5(3)-b5(3)))^2);
L6=sqrt((abs(a6(1)-b6(1)))^2+(abs(a6(2)-b6(2)))^2+(abs(a6(3)-b6(3)))^2);
Legs=[L1,L2,L3,L4,L5,L6];   %leg value return
platcoords=[b1(1),b1(2),b1(3),b2(1),b2(2),b2(3),b3(1),b3(2),b3(3),b4(1),b4(2),b4(3),b5(1),b5(2),b5(3),b6(1),b6(2),b6(3)]; %plat position return
animcoords=[b1t(1),b1t(2),b1t(3),b2t(1),b2t(2),b2t(3),b3t(1),b3t(2),b3t(3),b4t(1),b4t(2),b4t(3),b5t(1),b5t(2),b5t(3),b6t(1),b6t(2),b6t(3)]; %plat position return for animation
inv_return=[Legs,platcoords,animcoords]; %return
end

