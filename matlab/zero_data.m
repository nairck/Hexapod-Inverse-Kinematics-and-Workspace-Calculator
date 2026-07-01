function zero_data()
plotinfo=get(gcf,'UserData'); %load form data into plotinfo
set(plotinfo.rolldelta,'String','0.000');
set(plotinfo.pitchdelta,'String','0.000');
set(plotinfo.yawdelta,'String','0.000');
set(plotinfo.Pxvaldelta,'String','0.000');
set(plotinfo.Pyvaldelta,'String','0.000');
set(plotinfo.Pzvaldelta,'String','0.000');
color_input_box()
end