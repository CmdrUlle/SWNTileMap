@echo off
SET PixelScreenWidth=1895
SET PixelScreenHeight=1000
SET TileScreenWidth=-1
SET TileScreenHeight=-1
SET MapScreenWidth=100
SET MapScreenHeight=50
SET TileSize=15
SET levels=8
REM SET loadMap
SET overlayImage="Random"

python ./SWNTileMap.py ^
-px %PixelScreenWidth% ^
-py %PixelScreenHeight% ^
-tx %TileScreenWidth% ^
-ty %TileScreenHeight% ^
-mx %MapScreenWidth% ^
-my %MapScreenHeight% ^
-ts %TileSize% ^
-z %levels% ^
--OverlayImage %overlayImage%