function edit_Constraints()
plotinfo=get(gcf,'UserData'); %load form data into plotinfo
editConstraints_state=get(plotinfo.editConstraints_but,'Value');
if editConstraints_state==0
    set(plotinfo.rollmin,'enable','off')
    set(plotinfo.rollmax,'enable','off')
    set(plotinfo.pitchmin,'enable','off')
    set(plotinfo.pitchmax,'enable','off')
    set(plotinfo.yawmin,'enable','off')
    set(plotinfo.yawmax,'enable','off')
    set(plotinfo.pxmin,'enable','off')
    set(plotinfo.pxmax,'enable','off')
    set(plotinfo.pymin,'enable','off')
    set(plotinfo.pymax,'enable','off')
    set(plotinfo.pzmin,'enable','off')
    set(plotinfo.pzmax,'enable','off')
    set(plotinfo.jointmin,'enable','off')
    set(plotinfo.jointmax,'enable','off')
    set(plotinfo.actuatorLead,'enable','off')
elseif editConstraints_state==1
    set(plotinfo.rollmin,'enable','on')
    set(plotinfo.rollmax,'enable','on')
    set(plotinfo.pitchmin,'enable','on')
    set(plotinfo.pitchmax,'enable','on')
    set(plotinfo.yawmin,'enable','on')
    set(plotinfo.yawmax,'enable','on')
    set(plotinfo.pxmin,'enable','on')
    set(plotinfo.pxmax,'enable','on')
    set(plotinfo.pymin,'enable','on')
    set(plotinfo.pymax,'enable','on')
    set(plotinfo.pzmin,'enable','on')
    set(plotinfo.pzmax,'enable','on')
    set(plotinfo.jointmin,'enable','on')
    set(plotinfo.jointmax,'enable','on')
    set(plotinfo.actuatorLead,'enable','on')
end

end