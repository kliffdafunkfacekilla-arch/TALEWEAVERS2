import React, { useEffect, useRef, useState } from 'react';
import * as PIXI from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import { useGameStore } from '../store/useGameStore';
import { useWorldStore } from '../store/useWorldStore';
import { Delaunay } from 'd3-delaunay';

export const MapRenderer: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<PIXI.Application | null>(null);
    const viewportRef = useRef<Viewport | null>(null);
    const mapGraphicsRef = useRef<PIXI.Graphics | null>(null);
    const [texturesLoaded, setTexturesLoaded] = useState(false);
    const textureCache = useRef<Record<string, PIXI.Texture>>({});
    const tileCache = useRef<Record<string, PIXI.Texture[]>>({});

    const vttTier = useGameStore((state) => state.vttTier);
    const currentHexId = useGameStore((state) => state.currentHexId);

    const loadedHexes = useWorldStore((state) => state.loadedHexes);
    const viewLens = useWorldStore((state) => state.viewLens);
    const setSelectedHex = useWorldStore((state) => state.setSelectedHex);
    const fetchMapChunk = useWorldStore((state) => state.fetchMapChunk);

    // --- Tier 1: Parchment Colors ---
    const getParchmentColor = (biome: string, elevation: number) => {
        if (elevation <= 0.2) return 0xd4d4d8; // Muted parchment water
        switch (biome) {
            case 'DEEP_TUNDRA': return 0xffffff;
            case 'LUSH_JUNGLE': return 0xdcfce7;
            case 'SCORCHED_DESERT': return 0xfef9c3;
            default: return 0xf5f5f4; // Neutral paper
        }
    };

    // --- Tier 2: Vivid Colors (Fallback if no texture) ---
    const getVividColor = (biome: string, elevation: number) => {
        if (elevation <= 0.2) return elevation < 0.1 ? 0x0f172a : 0x0284c7;
        switch (biome) {
            case 'DEEP_TUNDRA': return 0xf1f5f9;
            case 'SCORCHED_DESERT': return 0xfde047;
            case 'LUSH_JUNGLE': return 0x166534;
            case 'MUSHROOM_SWAMP': return 0x9333ea;
            default: return 0x4ade80;
        }
    };

    const draw = () => {
        const mapGraphics = mapGraphicsRef.current;
        const viewport = viewportRef.current;
        if (!mapGraphics || !viewport || loadedHexes.length === 0) return;

        mapGraphics.clear();
        const bounds = viewport.getVisibleBounds();
        const padding = 20;
        const visibleHexes = loadedHexes.filter(h =>
            h.x >= bounds.x - padding &&
            h.x <= bounds.x + bounds.width + padding &&
            h.y >= bounds.y - padding &&
            h.y <= bounds.y + bounds.height + padding
        );

        if (visibleHexes.length === 0 && vttTier !== 4) return;

        const USE_FAST_DRAW = visibleHexes.length > 2500 || vttTier === 1;

        const renderCell = (cell: any, drawPoints: number[]) => {
            if (vttTier === 1) {
                // Tier 1: Ancient Paper Style
                const color = getParchmentColor(cell.biome_tag, cell.elevation);
                mapGraphics.fill(color);
                mapGraphics.poly(drawPoints);
                mapGraphics.stroke({ width: 0.5, color: 0x78716c, alpha: 0.4 });
                mapGraphics.fill();
                return;
            }

            // Tier 2: Regional / Tactical View
            if (viewLens === 'PHYSICAL') {
                let color = getVividColor(cell.biome_tag, cell.elevation);
                let texture = null;

                if (cell.biome_tag === 'LUSH_JUNGLE') texture = textureCache.current.forest;
                if (cell.biome_tag === 'SCORCHED_DESERT') texture = textureCache.current.desert;
                if (cell.elevation > 0.8) texture = textureCache.current.mountain;

                if (texture && texturesLoaded) {
                    mapGraphics.fill({ texture, color: 0xFFFFFF });
                } else {
                    mapGraphics.fill(color);
                }

                mapGraphics.poly(drawPoints);
                if (cell.elevation <= 0.2) {
                    mapGraphics.stroke({ width: 0.5, color: 0x0ea5e9, alpha: 0.3 });
                } else {
                    mapGraphics.stroke({ width: 0.2, color: 0x000000, alpha: 0.1 });
                }
                mapGraphics.fill();
            }
            else if (viewLens === 'POLITICAL') {
                let color = cell.elevation <= 0.2 ? 0x050505 : 0x1f1f22;
                if (cell.faction_owner === 'The_Rot_Coven') color = 0x7f1d1d;
                if (cell.faction_owner === 'Iron_Empire') color = 0x1e3a8a;
                mapGraphics.fill(color);
                mapGraphics.poly(drawPoints);
                mapGraphics.stroke({ width: 1, color: 0x000000, alpha: 0.5 });
                mapGraphics.fill();
            }
            else if (viewLens === 'RESOURCE') {
                mapGraphics.fill(0x09090b);
                mapGraphics.poly(drawPoints);
                mapGraphics.stroke({ width: 1, color: 0x27272a, alpha: 0.5 });
                mapGraphics.fill();
                if (cell.local_resources?.includes('Iron_Ore')) {
                    mapGraphics.fill(0xf97316); mapGraphics.circle(cell.x, cell.y, 4); mapGraphics.fill();
                }
            }
        };

        if (vttTier === 2) {
            // Tier 2: Regional (20x20 Strategic Grid)
            const grid = useWorldStore.getState().regionalGrid;
            if (!grid) return;
            const cellSize = 10;
            grid.grid.forEach((row: string[], r: number) => {
                row.forEach((type: string, c: number) => {
                    const hash = (r * 31 + c) % 3;
                    let texture = tileCache.current.grass?.[hash];

                    const isBuilding = ['SETTLEMENT', 'HOUSE', 'SHOP', 'TAVERN', 'OUTPOST'].includes(type);
                    if (isBuilding) texture = tileCache.current.dirt?.[0];

                    if (texture && texturesLoaded) {
                        mapGraphics.fill({ texture, color: 0xFFFFFF });
                    } else {
                        mapGraphics.fill(isBuilding ? 0xf59e0b : 0x4ade80);
                    }
                    mapGraphics.rect(c * cellSize, r * cellSize, cellSize, cellSize);
                    mapGraphics.fill();
                });
            });
            return;
        }

        if (vttTier === 3) {
            // Tier 3: Local (100x100 Exploration Grid)
            const grid = useWorldStore.getState().localGrid;
            if (!grid) return;
            const cellSize = 5;
            grid.grid.forEach((row: string[], r: number) => {
                row.forEach((type: string, c: number) => {
                    const hash = (r * 101 + c) % 3;
                    let texture = tileCache.current.grass?.[hash];
                    if (type === 'THICKET') texture = tileCache.current.swamp?.[hash % 2];

                    if (texture && texturesLoaded) {
                        mapGraphics.fill({ texture, color: 0xFFFFFF });
                    } else {
                        mapGraphics.fill(type === 'THICKET' ? 0x166534 : 0x22c55e);
                    }
                    mapGraphics.rect(c * cellSize, r * cellSize, cellSize, cellSize);
                    mapGraphics.fill();
                });
            });
            return;
        }

        if (vttTier === 4) {
            // Tier 4: Player/Tactical (100x100 5ft-scale Grid)
            const encounter = useWorldStore.getState().playerGrid;
            if (!encounter || !encounter.grid) return;
            const cellSize = 5;

            // Draw Grid Cells (Floors, Walls, Debris)
            encounter.grid.forEach((row: string[], r: number) => {
                row.forEach((type: string, c: number) => {
                    const hash = (r * 101 + c) % 3;
                    if (type === 'WALL') {
                        mapGraphics.fill(0x44403c); // Dark stone
                    } else if (type === 'FLOOR') {
                        mapGraphics.fill({ texture: tileCache.current.dirt?.[0], color: 0x92400e }); // Golden floor
                    } else if (type === 'DEBRIS') {
                        mapGraphics.fill(0x78716c);
                    } else {
                        // Ambient Outdoor tile
                        let texture = tileCache.current.grass?.[hash];
                        mapGraphics.fill({ texture, color: 0xFFFFFF });
                    }
                    mapGraphics.rect(c * cellSize, r * cellSize, cellSize, cellSize);
                    mapGraphics.fill();
                });
            });

            // Draw Tokens (Player, NPCs)
            if (encounter.tokens) {
                encounter.tokens.forEach((token: any) => {
                    mapGraphics.fill(token.isPlayer ? 0x3b82f6 : 0xf59e0b);
                    mapGraphics.circle(token.x * cellSize + cellSize / 2, token.y * cellSize + cellSize / 2, cellSize * 0.8);
                    mapGraphics.fill();
                    // Status text if relevant
                    if (token.status === "traveling") {
                        mapGraphics.stroke({ width: 0.5, color: 0xffffff });
                        mapGraphics.circle(token.x * cellSize + cellSize / 2, token.y * cellSize + cellSize / 2, cellSize);
                        mapGraphics.stroke();
                    }
                });
            }
            return;
        }

        if (!USE_FAST_DRAW) {
            const points = Float64Array.from(visibleHexes.flatMap((c: any) => [c.x, c.y]));
            const delaunay = Delaunay.from(points as any);
            const voronoi = delaunay.voronoi([bounds.x - 50, bounds.y - 50, bounds.x + bounds.width + 50, bounds.y + bounds.height + 50]);

            visibleHexes.forEach((cell: any, i: number) => {
                const polygon = voronoi.cellPolygon(i);
                if (!polygon || polygon.length < 3) return;
                const drawPoints: number[] = [];
                for (let j = 0; j < polygon.length - 1; j++) {
                    drawPoints.push(polygon[j][0], polygon[j][1]);
                }
                renderCell(cell, drawPoints);
            });
        } else {
            visibleHexes.forEach((cell: any) => {
                const color = vttTier === 1 ? getParchmentColor(cell.biome_tag, cell.elevation) : getVividColor(cell.biome_tag, cell.elevation);
                mapGraphics.fill(color);
                mapGraphics.circle(cell.x, cell.y, vttTier === 1 ? 0.5 : 0.7);
                mapGraphics.fill();
            });
        }

        // --- TRADE CARAVANS ---
        if (vttTier === 2) {
            const time = Date.now() * 0.001;
            loadedHexes.forEach(cell => {
                if (cell.road_next_id !== -1 && cell.settlement_name) {
                    const next = loadedHexes.find(h => h.id === cell.road_next_id);
                    if (next) {
                        const progress = (time % 5) / 5;
                        const cx = cell.x + (next.x - cell.x) * progress;
                        const cy = cell.y + (next.y - cell.y) * progress;

                        mapGraphics.fill({ color: 0xf59e0b, alpha: 0.8 });
                        mapGraphics.circle(cx, cy, 2);
                        mapGraphics.fill();

                        mapGraphics.fill({ color: 0xf59e0b, alpha: 0.2 });
                        mapGraphics.circle(cx, cy, 5);
                        mapGraphics.fill();
                    }
                }
            });
        }

        // --- TRAVEL PATH RENDERING ---
        const activePath = useWorldStore.getState().activePath;
        if (activePath && activePath.length > 1) {
            let cellSize = 5;
            if (vttTier === 2) cellSize = 10;

            mapGraphics.stroke({ width: 3, color: 0x3b82f6, alpha: 0.6 });
            mapGraphics.moveTo(activePath[0][0] * cellSize + cellSize / 2, activePath[0][1] * cellSize + cellSize / 2);
            for (let i = 1; i < activePath.length; i++) {
                mapGraphics.lineTo(activePath[i][0] * cellSize + cellSize / 2, activePath[i][1] * cellSize + cellSize / 2);
            }
            mapGraphics.stroke();

            // Draw Destination Glow
            const dest = activePath[activePath.length - 1];
            mapGraphics.fill({ color: 0x3b82f6, alpha: 0.3 });
            mapGraphics.circle(dest[0] * cellSize + cellSize / 2, dest[1] * cellSize + cellSize / 2, cellSize * 2);
            mapGraphics.fill();
        }

        // Draw Player Marker
        if (currentHexId !== null) {
            const playerHex = loadedHexes.find((c: any) => c.id === currentHexId);
            if (playerHex) {
                // ... (existing player marker logic)
                mapGraphics.fill({ color: 0xf59e0b, alpha: 0.3 });
                mapGraphics.circle(playerHex.x, playerHex.y, 8);
                mapGraphics.fill();
                mapGraphics.fill({ color: 0xf59e0b, alpha: 1 });
                mapGraphics.circle(playerHex.x, playerHex.y, 4);
                mapGraphics.stroke({ width: 2, color: 0xffffff, alpha: 1 });
                mapGraphics.fill();
            }
        }
    };

    // PIXI Lifecycle
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        let appInstance: PIXI.Application | null = null;
        let isDestroyed = false;

        const initPIXI = async () => {
            const app = new PIXI.Application();

            try {
                // Load Tier 2 Hex Textures
                const forest = await PIXI.Assets.load('/assets/forest_hex.png');
                const mountain = await PIXI.Assets.load('/assets/mountain_hex.png');
                const desert = await PIXI.Assets.load('/assets/desert_hex.png');
                textureCache.current = { forest, mountain, desert };

                // Load Tile Textures for Local/Tactical
                const grass = await Promise.all([0, 1, 2].map(i => PIXI.Assets.load(`/tiles/grass_${i}_new.png`)));
                const sand = await Promise.all([1, 2, 3].map(i => PIXI.Assets.load(`/tiles/sand_${i}.png`)));
                const swamp = await Promise.all([0, 1, 2].map(i => PIXI.Assets.load(`/tiles/swamp_${i}_new.png`)));
                const dirt = await Promise.all([0, 1, 2].map(i => PIXI.Assets.load(`/tiles/dirt_${i}_new.png`)));
                tileCache.current = { grass, sand, swamp, dirt };

                setTexturesLoaded(true);

                await app.init({
                    background: 0x050505,
                    resizeTo: container,
                    antialias: true,
                    resolution: window.devicePixelRatio || 1,
                    autoDensity: true,
                });

                if (isDestroyed) {
                    app.destroy(true, { children: true });
                    return;
                }

                container.appendChild(app.canvas as unknown as HTMLElement);
                appRef.current = app;
                appInstance = app;

                const WORLD_WIDTH = 1000;
                const WORLD_HEIGHT = 400;
                const viewport = new Viewport({
                    screenWidth: container.clientWidth,
                    screenHeight: container.clientHeight,
                    worldWidth: WORLD_WIDTH, worldHeight: WORLD_HEIGHT,
                    events: app.renderer.events
                });
                viewportRef.current = viewport;
                app.stage.addChild(viewport);
                viewport.drag().pinch().wheel().decelerate();

                viewport.moveCenter(WORLD_WIDTH / 2, WORLD_HEIGHT / 2);
                viewport.setZoom(0.5, true);

                // Animation Loop for Caravans
                app.ticker.add(() => {
                    const state = useGameStore.getState();
                    if (state.vttTier === 2) {
                        draw();
                    }
                });

                viewport.on('moved', () => draw());
                viewport.on('zoomed', () => {
                    const state = useGameStore.getState();
                    const worldStore = useWorldStore.getState();
                    const zoom = viewport.scale.x;
                    const setTier = state.setVttTier;
                    const currentHexId = state.currentHexId;

                    if (state.vttTier === 1 && zoom > 2) {
                        setTier(2);
                        state.addChatMessage({ sender: 'SYSTEM', text: 'ZOOMING INTO REGIONAL MAP...' });
                        worldStore.fetchRegionMap(currentHexId);
                    } else if (state.vttTier === 2) {
                        if (zoom < 1.5) {
                            setTier(1);
                        } else if (zoom > 8) {
                            setTier(3);
                            state.addChatMessage({ sender: 'SYSTEM', text: 'FOCUSING ON LOCAL SECTOR...' });
                            worldStore.fetchLocalGrid(currentHexId, 10, 10);
                        }
                    } else if (state.vttTier === 3) {
                        if (zoom < 5) {
                            setTier(2);
                        } else if (zoom > 15) {
                            setTier(4);
                            state.addChatMessage({ sender: 'SYSTEM', text: 'DROPPING INTO TACTICAL ENGAGEMENT...' });
                            worldStore.fetchTacticalGrid(currentHexId, 50, 50);
                        }
                    } else if (state.vttTier === 4 && zoom < 8) {
                        setTier(3);
                    }
                });

                const mapGraphics = new PIXI.Graphics();
                mapGraphicsRef.current = mapGraphics;
                viewport.addChild(mapGraphics);

                const handleInteraction = (e: any) => {
                    const gameState = useGameStore.getState();
                    const worldState = useWorldStore.getState();
                    const v = viewportRef.current;
                    const localPos = v.toLocal(e.global);

                    if (gameState.vttTier === 2) {
                        // Regional Pathfinding (20x20)
                        const cellSize = 10;
                        const rx = Math.floor(localPos.x / cellSize);
                        const ry = Math.floor(localPos.y / cellSize);
                        if (rx >= 0 && rx < 20 && ry >= 0 && ry < 20 && gameState.currentHexId) {
                            worldState.planTravel("REGIONAL", gameState.currentHexId, [10, 10], [rx, ry]);
                            gameState.addChatMessage({ sender: 'SYSTEM', text: `LOCAL DESTINATION: [${rx}, ${ry}]. Calculating travel time...` });
                        }
                        return;
                    }

                    if (gameState.vttTier === 3) {
                        // Local Pathfinding (100x100)
                        const cellSize = 5;
                        const lx = Math.floor(localPos.x / cellSize);
                        const ly = Math.floor(localPos.y / cellSize);
                        if (lx >= 0 && lx < 100 && ly >= 0 && ly < 100 && gameState.currentHexId) {
                            worldState.planTravel("LOCAL", gameState.currentHexId, [50, 50], [lx, ly], 10, 10);
                            gameState.addChatMessage({ sender: 'SYSTEM', text: `TACTICAL DESTINATION: [${lx}, ${ly}]. Estimating travel time...` });
                        }
                        return;
                    }

                    if (gameState.vttTier === 4) {
                        // Player Level (Tactical) - Move individual tokens
                        return;
                    }

                    // ... (existing world hex selection logic)
                    let minDist = Infinity;
                    let nearestId = -1;

                    for (let i = 0; i < worldState.loadedHexes.length; i++) {
                        const cell = worldState.loadedHexes[i];
                        const dx = cell.x - localPos.x;
                        const dy = cell.y - localPos.y;
                        const dist = dx * dx + dy * dy;
                        if (dist < minDist) { minDist = dist; nearestId = i; }
                    }

                    if (nearestId !== -1) {
                        const hex = worldState.loadedHexes[nearestId];
                        setSelectedHex(hex);

                        if (gameState.vttTier === 1) {
                            gameState.addChatMessage({ sender: 'SYSTEM', text: `HEX SELECTED: ${hex.settlement_name || 'Untamed Lands'} (ID: ${hex.id})` });
                        }
                    }
                };

                viewport.eventMode = 'static';
                viewport.hitArea = new PIXI.Rectangle(-5000, -5000, 10000, 10000);
                viewport.on('pointerdown', handleInteraction);

                draw();
            } catch (err) {
                console.error("[PIXI] Initialization failed:", err);
            }
        };

        initPIXI();

        return () => {
            isDestroyed = true;
            if (appInstance) {
                appInstance.destroy(true, { children: true });
                appRef.current = null;
                viewportRef.current = null;
                mapGraphicsRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        draw();
    }, [loadedHexes, viewLens, currentHexId, vttTier, texturesLoaded]);

    useEffect(() => {
        if (loadedHexes.length === 0) {
            fetchMapChunk(315, 315, 60);
        }
    }, [fetchMapChunk, loadedHexes.length]);

    useEffect(() => {
        if (currentHexId !== null) {
            const hex = loadedHexes.find(h => h.id === currentHexId);
            if (hex) {
                fetchMapChunk(hex.x, hex.y, 40);
            }
        }
    }, [currentHexId, fetchMapChunk, loadedHexes]);

    useEffect(() => {
        const worldState = useWorldStore.getState();
        if (currentHexId !== null) {
            if (vttTier === 2) worldState.fetchRegionMap(currentHexId);
            if (vttTier === 3) worldState.fetchLocalGrid(currentHexId, 10, 10); // Use campaign coords later
            if (vttTier === 4) worldState.fetchTacticalGrid(currentHexId, 50, 50);
        }
    }, [vttTier, currentHexId]);

    return <div ref={containerRef} className="w-full h-full" />;
};
