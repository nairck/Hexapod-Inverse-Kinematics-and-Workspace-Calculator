function handle_scaler_selection(scaler, dlg, plotinfo, homeNewOld)
% Retrieve plot info from main figure window
if isvalid(dlg)
    % Clear previous UI elements except Cancel
    children = get(dlg, 'Children');
    for c = children'
        tag = get(c, 'Tag');
        if ~strcmp(get(c, 'Style'), 'pushbutton') || ~strcmp(get(c, 'String'), 'Cancel')
            delete(c);
        end
    end
    if scaler <= 0.8
        stringScaler = 'HIGH (~10min)';
    elseif scaler > 0.8 && scaler <= 1.4
        stringScaler = 'MEDIUM (~1min)';
    else
        stringScaler = 'LOW (~5sec)';
    end
    uicontrol(dlg, 'Style', 'text', 'Position', [20 155 440 20], ...
        'String', sprintf('Solving workspace with %s resolution grid...', stringScaler));
    % Add a scrolling message box (if not already added)
    message_box = uicontrol(dlg, 'Style', 'edit', ...
        'Position', [20 40 450 120], ...
        'Max', 8, 'Enable', 'inactive', ...
        'HorizontalAlignment', 'left', ...
        'BackgroundColor', 'white', ...
        'FontSize', 9, ...
        'String', {'Starting computation...'});
    setappdata(0, 'workspace_message_box', message_box);
    % Run the drawing function and display status updates
    %     draw_orientation_workspace(scaler, plotinfo, homeNewOld);  % Pass plotinfo along with scaler
    draw_orientation_workspace_spherical(scaler, plotinfo, homeNewOld);  % Pass plotinfo along with scaler 
end
end