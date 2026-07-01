function pos = centerfig(width,height)
screen_s = get(0,'ScreenSize');
pos = [screen_s(3)/2 - width/2, screen_s(4)/2 - height/2, width, height];
end