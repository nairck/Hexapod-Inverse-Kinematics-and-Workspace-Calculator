function load_data()
%LOAD_DATA  Ensure formdata.txt exists and is valid (3‑decimals “tag = value” plus calculator_name),
%offer Create/Quit if missing, validate format if present, populate GUI or close.

    hMain = gcf;
    plotinfo = get(hMain,'UserData');
    fname = 'formdata.txt';

    %--- 1) Tags & defaults ---
    tags = {
      'base1x','base1y','base2x','base2y','base3x','base3y','base4x','base4y', ...
      'base5x','base5y','base6x','base6y','baseZ', ...
      'plat1x','plat1y','plat2x','plat2y','plat3x','plat3y','plat4x','plat4y', ...
      'plat5x','plat5y','plat6x','plat6y','platZheight', ...
      'rollmin','rollmax','pitchmin','pitchmax','yawmin','yawmax', ...
      'pxmin','pxmax','pymin','pymax','pzmin','pzmax', ...
      'leg1_old','leg2_old','leg3_old','leg4_old','leg5_old','leg6_old', ...
      'leg1','leg2','leg3','leg4','leg5','leg6', ...
      'roll_old','pitch_old','yaw_old','Pxval_old','Pyval_old','Pzval_old', ...
      'roll','pitch','yaw','Pxval','Pyval','Pzval', ...
      'benchZheight','jointmin','jointmax','benchThickness','zpdLegLength', ...
      'platToBenchBottomZ','actuatorLead'
    };
    default_values = [ ...
        -1487.250;  -108.110; -1487.250;  158.110;  -390.100;   533.220; ...
        -159.550;   400.110;  -159.550;  -350.110;  -390.100;  -483.220; ...
        -375.910;  -1487.250;   -3.100;  -1487.250;    53.100;  -299.160; ...
         480.720;  -250.490;   452.620;  -250.490;  -402.620;  -299.160; ...
        -430.720;  -263.444;    -2.650;     2.650;    -1.150;     1.150; ...
         -1.500;     1.500;   -28.000;    28.000;   -28.000;    28.000; ...
         -20.000;    20.000;   153.869;   153.869;   153.867;   153.870; ...
         153.870;   153.867;   153.869;   153.869;   153.867;   153.870; ...
         153.870;   153.867;     0.000;     0.000;     0.000;     0.000; ...
           0.000;     0.000;     0.000;     0.000;     0.000;     0.000; ...
           0.000;     0.000;  -124.000;   -18.000;    18.000;   110.000; ...
         153.866;    29.444;     3.000
    ];
    defaultName = 'Hexapod Inverse Kinematics and Workspace Solver';
    
    N = numel(tags);
    totalLines = N + 1;  % plus calculator_name

    %--- 2) If missing, Create or Quit ---
    if ~isfile(fname)
        prompt = sprintf( ...
          'formdata.txt not found in:\n%s\n\nCreate default file and proceed, or Quit to supply your own?', pwd);
        choice = questdlg(prompt,'File Missing','Create','Quit','Create');
        if isempty(choice) || strcmp(choice,'Quit')
            close(hMain); return;
        end
        fid = fopen(fname,'w');
        for ii=1:N
            fprintf(fid,'%s = %.3f\n', tags{ii}, default_values(ii));
        end
        fprintf(fid, 'calculator_name = ''%s''\n', defaultName);
        fclose(fid);
    end

    %--- 3) Read lines ---
    fid = fopen(fname,'r');
    rawLines = {};
    t = fgetl(fid);
    while ischar(t)
        rawLines{end+1,1} = strtrim(t);
        t = fgetl(fid);
    end
    fclose(fid);

    %--- 4) Validate format & collect ---
    vals   = zeros(N,1);
    errors = {};

    if numel(rawLines) ~= totalLines
        errors{end+1} = sprintf('Expected %d lines but found %d.', totalLines, numel(rawLines));
    end
    % Numeric lines 1..N
    for ii = 1:min(N,numel(rawLines))
        expected = sprintf('%s = -123.456', tags{ii});
        pat = sprintf('^%s = (-?\\d+\\.\\d{3})$', tags{ii});
        tok = regexp(rawLines{ii}, pat, 'tokens');
        if isempty(tok)
            errors{end+1} = sprintf('Line %d: ''%s''  — Expected: ''%s''', ...
                                   ii, rawLines{ii}, expected);
        else
            v = str2double(tok{1}{1});
            if isnan(v)
                errors{end+1} = sprintf('Line %d: non-numeric ''%s''', ii, rawLines{ii});
            else
                vals(ii) = v;
            end
        end
    end
    % Calculator name on line N+1
    if numel(rawLines) >= N+1
        line = rawLines{N+1};
        expectedName = sprintf('calculator_name = ''%s''', defaultName);
        patName = '^calculator_name = ''(.{1,100})''$';
        tok = regexp(line, patName, 'tokens');
        if isempty(tok)
            errors{end+1} = sprintf('Line %d: ''%s''  — Expected: ''%s''', ...
                                   N+1, line, expectedName);
        else
            calcName = tok{1}{1};
        end
    end

    %--- 5) If errors, preview up to 4, Overwrite/Quit ---
    if ~isempty(errors)
        previewCount = min(4,numel(errors));
        txt = strjoin(errors(1:previewCount), '\n');
        if numel(errors)>previewCount
            txt = [txt sprintf('\n...and %d more invalid lines', numel(errors)-previewCount)];
        end
        msg = sprintf(['Invalid formdata.txt detected.\n' ...
                       'Issues (expected "tag = -123.456" or valid name):\n\n%s\n\n' ...
                       'Overwrite with defaults or Quit to fix?'], txt);
        choice = questdlg(msg,'Corrupted Formdata','Overwrite','Quit','Quit');
        if isempty(choice) || strcmp(choice,'Quit')
            close(hMain); return;
        end
        % Overwrite defaults
        fid = fopen(fname,'w');
        for ii=1:N
            fprintf(fid,'%s = %.3f\n', tags{ii}, default_values(ii));
        end
        fprintf(fid, 'calculator_name = ''%s''\n', defaultName);
        fclose(fid);
        vals = default_values(:);
        calcName = defaultName;
    end

    %--- 6) Populate GUI numeric fields ---
    for ii=1:N
        set(plotinfo.(tags{ii}), 'String', num2str(vals(ii),'%.3f'));
    end

    %--- 7) Apply calculator_name ---
    plotinfo.calculator_name = calcName;
    set(hMain,'Name',calcName);

    set(hMain,'UserData',plotinfo);

    %--- 8) Recompute deltas & refresh visuals ---
    oldR = str2double(get(plotinfo.roll_old,'String'));
    newR = str2double(get(plotinfo.roll,'String'));
    if oldR == newR
        zero_data();
    else
        prim = {'roll','pitch','yaw','Pxval','Pyval','Pzval'};
        for k = 1:numel(prim)
            prev = str2double(get(plotinfo.([prim{k} '_old']),'String'));
            curr = str2double(get(plotinfo.(prim{k}),'String'));
            set(plotinfo.([prim{k} 'delta']), 'String', num2str(curr-prev,'%.3f'));
        end
    end

    zpd = str2double(get(plotinfo.zpdLegLength,'String'));
    for j = 1:6
        prevL = str2double(get(plotinfo.(sprintf('leg%d_old',j)),'String'));
        currL = str2double(get(plotinfo.(sprintf('leg%d',j)),'String'));
        set(plotinfo.(sprintf('leg%ddelta',j)),    'String', num2str(currL-prevL,'%.3f'));
        set(plotinfo.(sprintf('leg%dabsdelta',j)), 'String', num2str(currL-zpd,   '%.3f'));
        ang = (currL-prevL) * 360 / str2double(get(plotinfo.actuatorLead,'String'));
        set(plotinfo.(sprintf('leg%dangledelta',j)),'String',num2str(ang,'%.3f'));
    end

    color_input_box();
end
