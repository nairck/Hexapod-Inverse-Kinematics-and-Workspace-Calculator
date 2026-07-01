function color_input_box()
plotinfo=get(gcf,'UserData');
if (str2double(get(plotinfo.leg1absdelta,'String')) < str2double(get(plotinfo.jointmin,'String'))) || (str2double(get(plotinfo.leg1absdelta,'String')) > str2double(get(plotinfo.jointmax,'String')))
    set(plotinfo.leg1absdelta,'ForegroundColor','#FF0000')
else
    set(plotinfo.leg1absdelta,'ForegroundColor','#77AC30')
end
if (str2double(get(plotinfo.leg2absdelta,'String')) < str2double(get(plotinfo.jointmin,'String'))) || (str2double(get(plotinfo.leg2absdelta,'String')) > str2double(get(plotinfo.jointmax,'String')))
    set(plotinfo.leg2absdelta,'ForegroundColor','#FF0000')
else
    set(plotinfo.leg2absdelta,'ForegroundColor','#77AC30')
end
if (str2double(get(plotinfo.leg3absdelta,'String')) < str2double(get(plotinfo.jointmin,'String'))) || (str2double(get(plotinfo.leg3absdelta,'String')) > str2double(get(plotinfo.jointmax,'String')))
    set(plotinfo.leg3absdelta,'ForegroundColor','#FF0000')
else
    set(plotinfo.leg3absdelta,'ForegroundColor','#77AC30')
end
if (str2double(get(plotinfo.leg4absdelta,'String')) < str2double(get(plotinfo.jointmin,'String'))) || (str2double(get(plotinfo.leg4absdelta,'String')) > str2double(get(plotinfo.jointmax,'String')))
    set(plotinfo.leg4absdelta,'ForegroundColor','#FF0000')
else
    set(plotinfo.leg4absdelta,'ForegroundColor','#77AC30')
end
if (str2double(get(plotinfo.leg5absdelta,'String')) < str2double(get(plotinfo.jointmin,'String'))) || (str2double(get(plotinfo.leg5absdelta,'String')) > str2double(get(plotinfo.jointmax,'String')))
    set(plotinfo.leg5absdelta,'ForegroundColor','#FF0000')
else
    set(plotinfo.leg5absdelta,'ForegroundColor','#77AC30')
end
if (str2double(get(plotinfo.leg6absdelta,'String')) < str2double(get(plotinfo.jointmin,'String'))) || (str2double(get(plotinfo.leg6absdelta,'String')) > str2double(get(plotinfo.jointmax,'String')))
    set(plotinfo.leg6absdelta,'ForegroundColor','#FF0000')
else
    set(plotinfo.leg6absdelta,'ForegroundColor','#77AC30')
end
end