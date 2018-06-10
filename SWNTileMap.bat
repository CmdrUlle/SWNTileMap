@echo off
SET PixelScreenWidth=1895
SET PixelScreenHeight=1000
SET TileScreenWidth=-1
SET TileScreenHeight=-1
SET MapScreenWidth=53
SET MapScreenHeight=27
SET TileSize=35
SET levels=8

python ./SWNTileMap.py ^
-px %PixelScreenWidth% ^
-py %PixelScreenHeight% ^
-tx %TileScreenWidth% ^
-ty %TileScreenHeight% ^
-mx %MapScreenWidth% ^
-my %MapScreenHeight% ^
-ts %TileSize% ^
-z %levels%