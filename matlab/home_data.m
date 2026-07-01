function home_data()
    % Load plotinfo from current figure
    plotinfo = get(gcf, 'UserData');
    fmt = '%.3f';

    % Read current GUI posture values (convert string to number)
    roll  = str2double(get(plotinfo.roll,  'String'));
    pitch = str2double(get(plotinfo.pitch, 'String'));
    yaw   = str2double(get(plotinfo.yaw,   'String'));
    px    = str2double(get(plotinfo.Pxval, 'String'));
    py    = str2double(get(plotinfo.Pyval, 'String'));
    pz    = str2double(get(plotinfo.Pzval, 'String'));

    % Set deltas to negative of current values
    set(plotinfo.rolldelta,   'String', sprintf(fmt, -roll));
    set(plotinfo.pitchdelta,  'String', sprintf(fmt, -pitch));
    set(plotinfo.yawdelta,    'String', sprintf(fmt, -yaw));
    set(plotinfo.Pxvaldelta,  'String', sprintf(fmt, -px));
    set(plotinfo.Pyvaldelta,  'String', sprintf(fmt, -py));
    set(plotinfo.Pzvaldelta,  'String', sprintf(fmt, -pz));

    color_input_box();  % Refresh input box colors if needed
end
