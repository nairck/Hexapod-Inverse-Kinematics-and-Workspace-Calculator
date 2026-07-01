function draw_plat(plat_coords)
% DRAW_PLAT   Draw hexapod base, platform, and legs in 3D
%
%   draw_plat(plat_coords) reads the base coordinates from the GUI,
%   uses plat_coords (1×18) for the platform, and redraws
%   the entire mechanism cleanly and efficiently.

% clear and prepare axes
cla; hold on;
axis vis3d equal off
rotate3d on
plotinfo = get(gcf,'UserData');

%── Read base points from GUI ───────────────────────────────────────────
baseZ = str2double( get(plotinfo.baseZ, 'String') );
base_x = arrayfun(@(i) ...
    str2double(get(plotinfo.(sprintf('base%dx',i)),'String')), 1:6);
base_y = arrayfun(@(i) ...
    str2double(get(plotinfo.(sprintf('base%dy',i)),'String')), 1:6);
basePts = [ base_x; base_y; baseZ*ones(1,6) ];   % 3×6

%── Read platform points from input vector ──────────────────────────────
% plat_coords = [x1 y1 z1, x2 y2 z2, … , x6 y6 z6]
platPts = reshape(plat_coords, 3, 6);             % 3×6

line_size  = 2;
arrow_len  = 150;

%── Draw coordinate axes ────────────────────────────────────────────────
plot3([0 0],[0 0],[0 arrow_len], '-^k', 'LineWidth',1, 'MarkerSize',3);
plot3([0 0],[0 arrow_len],[0 0], '->k', 'LineWidth',1, 'MarkerSize',3);
plot3([0 arrow_len],[0 0],[0 0], '->k', 'LineWidth',1, 'MarkerSize',3);
text(0,0,arrow_len, 'Z','FontSize',8, 'HorizontalAlignment','center', 'VerticalAlignment','bottom');
text(0,arrow_len,0, 'Y','FontSize',8, 'HorizontalAlignment','center', 'VerticalAlignment','bottom');
text(arrow_len,0,0, 'X','FontSize',8, 'HorizontalAlignment','center', 'VerticalAlignment','bottom');

%── Draw base triangular edges as persistent line handles ─────────
baseEdges = [2 3; 4 5; 6 1];
for e = 1:3
    i1 = baseEdges(e,1); i2 = baseEdges(e,2);
    % create the line once, store it in plotinfo.p13..p15
    plotinfo.(sprintf('p%d',12+e)) = plot3( ...
        basePts(1,[i1 i2]), ...
        basePts(2,[i1 i2]), ...
        basePts(3,[i1 i2]), ...
        '-b','LineWidth',line_size,'Color','#00008b' ...
        );
end
set(gcf,'UserData',plotinfo);


%── Draw legs from base → platform ──────────────────────────────────────
legColors = {'#0072BD','#D95319','#EDB120','#7E2F8E','#77AC30','#4DBEEE'};
for i = 1:6
    style = '-.';  % only the first leg is dashed in your original code
    if i > 1, style = '-'; end
    plotinfo.(sprintf('p%d',i)) = plot3( ...
        [basePts(1,i) platPts(1,i)], ...
        [basePts(2,i) platPts(2,i)], ...
        [basePts(3,i) platPts(3,i)], ...
        style, 'Marker','o', 'MarkerSize',3, ...
        'LineWidth',line_size, 'Color',legColors{i} ...
        );
end

%── Draw platform hexagon edges (1–2,2–3,…,6–1) ────────────────────────
platformEdges = [1 2; 2 3; 3 4; 4 5; 5 6; 6 1];
for e = 1:size(platformEdges,1)
    i1 = platformEdges(e,1); i2 = platformEdges(e,2);
    idx = e + 6;  % handles p7…p12
    plotinfo.(sprintf('p%d',idx)) = plot3( ...
        [platPts(1,i1) platPts(1,i2)], ...
        [platPts(2,i1) platPts(2,i2)], ...
        [platPts(3,i1) platPts(3,i2)], ...
        '-r', 'MarkerSize',3, 'LineWidth',line_size, 'Color','#A2142F' ...
        );
end

%── Store updated handles and finish ────────────────────────────────────
set(gcf,'UserData',plotinfo);
end
