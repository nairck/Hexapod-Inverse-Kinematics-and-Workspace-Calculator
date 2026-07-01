function overwrite_data()
%OVERWRITE_DATA Copy “new” values to “old” and recompute deltas, all with three decimals

    pi = get(gcf,'UserData');
    getVal = @(f) str2double(get(pi.(f),'String'));
    fmt = '%.3f';

    % 1) Overwrite old leg lengths with current values
    for k = 1:6
        val = getVal(sprintf('leg%d',k));
        set(pi.(sprintf('leg%d_old',k)), 'String', sprintf(fmt, val));
    end

    % 2) Overwrite old posture with current values
    posture = {'roll','pitch','yaw','Pxval','Pyval','Pzval'};
    for i = 1:numel(posture)
        f = posture{i};
        val = getVal(f);
        set(pi.(sprintf('%s_old',f)), 'String', sprintf(fmt, val));
    end

    % 3) Recompute deltas: new - old
    %    and absolute deltas: new - ZPD leg length
    zpd = getVal('zpdLegLength');
    for k = 1:6
        newL = getVal(sprintf('leg%d',k));
        oldL = getVal(sprintf('leg%d_old',k));
        delta    = newL - oldL;
        absdelta = newL - zpd;
        angdelta = delta * 360 / getVal('actuatorLead');
        set(pi.(sprintf('leg%ddelta',     k)), 'String', sprintf(fmt, delta));
        set(pi.(sprintf('leg%dabsdelta',  k)), 'String', sprintf(fmt, absdelta));
        set(pi.(sprintf('leg%dangledelta',k)), 'String', sprintf(fmt, angdelta));
    end

    % 4) Clear input-focus changes and recolor
    zero_data();
     solve_inverse();
    color_input_box();
end
