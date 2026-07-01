function openAdjustDlg(field)
mainFig = gcf;
key     = [field '_totalOffset'];
prev    = getappdata(mainFig,key);
if isempty(prev), prev = 0; end

dlgW = 350; dlgH = 150;
d2 = dialog('Position',[0 0 dlgW dlgH],'Name','Adjust ZPD','WindowStyle','normal');
movegui(d2,'center');

% question line
axisChar = upper(field(1));
if endsWith(field,'mi'), prefix = 'platform'; else prefix = 'base'; end
txt1 = sprintf('Add or subtract %s value from all %s (%s) joints:',axisChar,prefix,field);
uicontrol(d2,'Style','text', 'Position',[20 dlgH-40 dlgW-40 20], ...
    'String',txt1,'HorizontalAlignment','center');

%–– Previous total, with commas and sign ––
s     = sprintf('%.3f', prev);
parts = strsplit(s,'.');
intp  = parts{1};  decp = parts{2};
signChar = '';% extract leading sign if any
if any(intp(1)=='-+')
    signChar = intp(1);
    intp = intp(2:end);
end
rev    = fliplr(intp);% format the absolute integer part with commas
chunks = regexp(rev,'\d{1,3}','match');
revC   = strjoin(chunks,',');
intC   = fliplr(revC);
numstr = [signChar intC '.' decp];% reassemble with sign and decimal
uicontrol(d2,'Style','text', ...
    'Position',[20 dlgH-70 dlgW-40 20], ...
    'String',sprintf('Total offset so far: %s mm', numstr), ...
    'HorizontalAlignment','center','FontAngle','italic');


% input box, pre‑fill with 0 rounded to 3 decimals
editHndl = uicontrol(d2,'Style','edit','Position',[100 dlgH-100 150 25], ...
    'String',sprintf('%.3f',0),...
    'BackgroundColor','white','HorizontalAlignment','center');

% buttons
uicontrol(d2,'Style','pushbutton','String','Update ZPD', ...
    'Position',[70 10 100 30], ...
    'Callback',@(s,e)applyAdjust(mainFig,field,editHndl,d2));
uicontrol(d2,'Style','pushbutton','String','Cancel', ...
    'Position',[180 10 100 30], ...
    'Callback',@(s,e)delete(d2));
end

