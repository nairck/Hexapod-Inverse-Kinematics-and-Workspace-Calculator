function yes_callback(input_box, dialog_handle, selector, newOrRecall)
val = str2double(get(input_box, 'String'));
if isnan(val) || val < 1 || val > 360
    errordlg('Please enter a valid numeric value between 1 and 360.', 'Invalid Input');
    return;
elseif (selector == 0)
    delete(dialog_handle); % Close dialog
    export_orientation_workspace(val,newOrRecall);
elseif (selector == 1)
    delete(dialog_handle); % Close dialog
    export_reachable_workspace(val,newOrRecall);
else
    return;
end
end
