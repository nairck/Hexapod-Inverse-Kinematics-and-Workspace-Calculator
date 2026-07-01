function save_data()
%SAVE_DATA  Write all plotinfo numeric fields and calculator_name back into formdata.txt
% If unable to open formdata.txt, falls back to creating formdata_new.txt.

    plotinfo = get(gcf,'UserData');
    fname = 'formdata.txt';
    
    % List of numeric tags
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
        'benchZheight','jointmin','jointmax','benchThickness','zpdLegLength',...
        'platToBenchBottomZ', 'actuatorLead'
    };
    
    % Try to open the primary file
    fid = fopen(fname,'w');
    if fid < 0
        % Fallback to a new file
        fallback = 'formdata_new.txt';
        %         warning('Could not open %s; saving to %s instead.', fname, fallback);
        fid = fopen(fallback,'w');
        if fid < 0
            error('Unable to open %s for writing.', fallback);
        end
    end
    
    % Write numeric tags with three decimals
    for i = 1:numel(tags)
        tag = tags{i};
        val = str2double(get(plotinfo.(tag),'String'));
        fprintf(fid, '%s = %.3f\n', tag, val);
    end
    
    % Write calculator_name (as loaded at startup)
    fprintf(fid, 'calculator_name = ''%s''\n', plotinfo.calculator_name);
    
    fclose(fid);
end
