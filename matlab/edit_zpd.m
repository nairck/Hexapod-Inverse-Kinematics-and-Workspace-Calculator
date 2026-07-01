function edit_zpd()
    pi = get(gcf,'UserData');
    editing = logical(get(pi.editzpd_but,'Value'));

    % Define groups of controls
    baseFields = arrayfun(@(i) {sprintf('base%dx',i), sprintf('base%dy',i)}, 1:6, 'Uni',false);
    platFields = arrayfun(@(i) {sprintf('plat%dx',i), sprintf('plat%dy',i)}, 1:6, 'Uni',false);
    benchCalc   = {'benchZheight'};                  % computed field
    zpdControls = {'benchThickness','zpdLegLength','platToBenchBottomZ'};

    % Flatten lists
    allFields = [ {'baseZ'}, baseFields{:}, {'platZheight'}, platFields{:}, benchCalc, zpdControls ];

    if ~editing
        % Turn everything off
        cellfun(@(f) set(pi.(f),'Enable','off'), allFields);

        % Compute benchZheight = platZheight + benchThickness + platToBenchBottomZ
        val = sum([ str2double(get(pi.platZheight,'String')), ...
                    str2double(get(pi.benchThickness,'String')), ...
                    str2double(get(pi.platToBenchBottomZ,'String')) ]);
        set(pi.benchZheight, 'String', num2str(val,'%.3f'));

    else
        % Turn base & platform & ZPD controls on, benchZheight stays off
        onFields = [{'baseZ'}, baseFields{:}, {'platZheight'}, platFields{:}, zpdControls];
        cellfun(@(f) set(pi.(f),'Enable','on'), onFields);
        set(pi.benchZheight,'Enable','off');
    end
end
