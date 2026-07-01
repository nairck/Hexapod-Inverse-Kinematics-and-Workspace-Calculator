function update_status(msg)
% Get the message box
box = getappdata(0, 'workspace_message_box');
if isgraphics(box)
    % Get the current text in the message box
    old_text = get(box, 'String');
    % If the old text is not already a cell array, convert it
    if ischar(old_text)
        old_text = {old_text};
    end
    % Prepend the new message to the existing text
    new_text = [{msg}; old_text];
    % Update the message box with the new text
    set(box, 'String', new_text);
    % Ensure the display is updated
    drawnow;
end
end