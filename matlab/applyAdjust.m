function applyAdjust(mainFig,field,editHndl,d2)
    v = str2double(get(editHndl,'String'));
    if isnan(v)
        errordlg('Please enter a numeric value.','Invalid Input');
        return;
    end

    % grab & update the running total on mainFig
    key  = [field '_totalOffset'];
    prev = getappdata(mainFig,key);
    if isempty(prev), prev = 0; end
    total = prev + v;
    setappdata(mainFig,key,total);

    % apply to the six controls
    pi = get(mainFig,'UserData');
    switch field
      case 'xsi', names = arrayfun(@(k)sprintf('base%dx',k),1:6,'Uni',false);
      case 'ysi', names = arrayfun(@(k)sprintf('base%dy',k),1:6,'Uni',false);
      case 'xmi', names = arrayfun(@(k)sprintf('plat%dx',k),1:6,'Uni',false);
      case 'ymi', names = arrayfun(@(k)sprintf('plat%dy',k),1:6,'Uni',false);
    end
    for fn = names
        h   = pi.(fn{1});
        old = str2double(get(h,'String'));
        set(h,'String',sprintf('%.3f',old+v));
    end

    % recompute benchZheight
    newVal = str2double(get(pi.platZheight,'String')) + ...
             str2double(get(pi.benchThickness,'String')) + ...
             str2double(get(pi.platToBenchBottomZ,'String'));
    set(pi.benchZheight,'String',sprintf('%.3f',newVal));

    delete(d2);
    solve_inverse();
end
