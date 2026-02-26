import { useEffect, useRef, useCallback } from 'react';
import { Application, Graphics, Container } from 'pixi.js';
import { useGameStore } from '../store/useGameStore';
import type { HexCell } from '../store/useGameStore';

// --- COLOR MAPPING ---
const getBiomeColor = (biome: string, elevation: number): number => {
    if (elevation <= 0.05) return 0x1E3A8A; // Deep Ocean Blue

    switch (biome) {
        case 'DEEP_TUNDRA': return 0xE0F2FE; // Ice White
        case 'SCORCHED_DESERT': return 0xFBBF24; // Sand Yellow
        case 'LUSH_JUNGLE': return 0x065F46; // Deep Green
        case 'MUSHROOM_SWAMP': return 0x4C1D95; // Toxic Purple
        case 'WASTELAND': return 0x52525B; // Ash Grey
        case 'OCEAN': return 0x1E3A8A; // Ocean Blue
        default: return 0x22C55E; // Default Grass
    }
};

export function MapRenderer() {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const cameraRef = useRef<Container | null>(null);
    const worldData = useGameStore((s) => s.worldData);
    const setSelectedHex = useGameStore((s) => s.setSelectedHex);

    const draw = useCallback(() => {
        const app = appRef.current;
        const camera = cameraRef.current;
        if (!app || !camera) return;

        // Clear previous drawings
        while (camera.children.length > 0) {
            camera.removeChildAt(0);
        }

        if (!worldData || !worldData.macro_map) return;

        const graphics = new Graphics();
        camera.addChild(graphics);

        worldData.macro_map.forEach((cell: any) => {
            const cx = cell.x;
            const cy = cell.y;
            const color = getBiomeColor(cell.biome_tag, cell.elevation);

            // Draw hexagon polygon (radius ~12px)
            const size = 12;
            const points: number[] = [];
            for (let a = 0; a < 6; a++) {
                const angle = (Math.PI / 3) * a;
                points.push(cx + size * Math.cos(angle));
                points.push(cy + size * Math.sin(angle));
            }

            graphics.poly(points);
            graphics.fill(color);

            // Snowcap borders for mountains, soft borders for everything else
            if (cell.elevation > 0.8) {
                graphics.poly(points);
                graphics.stroke({ width: 2, color: 0xFFFFFF, alpha: 0.5 });
            } else {
                graphics.poly(points);
                graphics.stroke({ width: 1, color: 0x000000, alpha: 0.2 });
            }

            // Red dot for settlements
            if (cell.settlement_name) {
                graphics.circle(cx, cy, 4);
                graphics.fill(0xFF0000);
            }
        });

        // Center camera on the map
        camera.x = app.screen.width / 2 - 500;
        camera.y = app.screen.height / 2 - 500;
    }, [worldData]);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        let cancelled = false;
        const app = new Application();

        app.init({
            background: 0x050505,
            resizeTo: el,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
        }).then(() => {
            if (cancelled) {
                app.destroy(true);
                return;
            }
            el.appendChild(app.canvas as HTMLCanvasElement);
            appRef.current = app;

            // Create camera container for pan/zoom
            const camera = new Container();
            app.stage.addChild(camera);
            cameraRef.current = camera;

            // Interactivity setup
            app.stage.eventMode = 'static';
            app.stage.hitArea = { contains: () => true };

            let isDragging = false;
            let dragStart = { x: 0, y: 0 };
            let clickStart = { x: 0, y: 0 };

            app.stage.on('pointerdown', (e) => {
                isDragging = true;
                dragStart = { x: e.global.x - camera.x, y: e.global.y - camera.y };
                clickStart = { x: e.global.x, y: e.global.y };
            });

            app.stage.on('pointerup', (e) => {
                isDragging = false;

                // If mouse moved less than 5px, it was a CLICK not a DRAG
                const distMoved = Math.hypot(e.global.x - clickStart.x, e.global.y - clickStart.y);

                if (distMoved < 5) {
                    const currentWorldData = useGameStore.getState().worldData;
                    if (currentWorldData && currentWorldData.macro_map) {
                        // Convert screen coords to world coords (accounting for zoom and pan)
                        const localClick = camera.toLocal(e.global);

                        let closestCell: HexCell | null = null;
                        let minDistance = Infinity;

                        // Voronoi nearest-neighbor: find closest hex center
                        currentWorldData.macro_map.forEach((cell: HexCell) => {
                            const dist = Math.hypot(cell.x - localClick.x, cell.y - localClick.y);
                            if (dist < minDistance) {
                                minDistance = dist;
                                closestCell = cell;
                            }
                        });

                        if (closestCell) {
                            useGameStore.getState().setSelectedHex(closestCell);
                        }
                    }
                }
            });

            app.stage.on('pointerupoutside', () => (isDragging = false));
            app.stage.on('pointermove', (e) => {
                if (isDragging) {
                    camera.x = e.global.x - dragStart.x;
                    camera.y = e.global.y - dragStart.y;
                }
            });

            // Zoom via mouse wheel
            el.addEventListener('wheel', (e) => {
                e.preventDefault();
                const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
                camera.scale.x *= zoomFactor;
                camera.scale.y *= zoomFactor;
            });

            draw();
        });

        return () => {
            cancelled = true;
            if (appRef.current) {
                appRef.current.destroy(true);
            });

    containerRef.current.appendChild(app.view as unknown as HTMLElement);
    appRef.current = app;

    const viewport = new Viewport({
        screenWidth: containerRef.current.clientWidth,
        screenHeight: containerRef.current.clientHeight,
        worldWidth: 2000,
        worldHeight: 2000,
        events: app.renderer.events
    });

    app.stage.addChild(viewport);
    viewport.drag().pinch().wheel().decelerate();

    const mapGraphics = new PIXI.Graphics();
    viewport.addChild(mapGraphics);

    // --- THE AZGAAR DRAG-PAINTING MATH ---
    let isPainting = false;
    let lastPaintedId = -1;

    viewport.eventMode = 'static';
    viewport.hitArea = new PIXI.Rectangle(-5000, -5000, 10000, 10000); // Massive hit area

    const handleInteraction = (e: any) => {
        const state = useGameStore.getState();
        if (!state.worldData) return;

        // 1. Get exact mouse coordinates inside the zoomable viewport
        const localPos = viewport.toLocal(e.global);

        // 2. Find the nearest hex via simple O(N) distance check (Lightning fast in JS)
        let minDist = Infinity;
        let nearestId = -1;

        for (let i = 0; i < state.worldData.macro_map.length; i++) {
            const cell = state.worldData.macro_map[i];
            const dx = cell.x - localPos.x;
            const dy = cell.y - localPos.y;
            const dist = dx * dx + dy * dy;

            if (dist < minDist) {
                minDist = dist;
                nearestId = i;
            }
        }

        // 3. Either Inspect it or Paint it!
        if (nearestId !== -1) {
            if (state.editMode === 'NONE') {
                setSelectedHex(state.worldData.macro_map[nearestId]);
            } else if (isPainting && nearestId !== lastPaintedId && state.activeBrush !== '') {
                lastPaintedId = nearestId;
                editHex(nearestId, state.editMode, state.activeBrush);
            }
        }
    };

    viewport.on('pointerdown', (e) => {
        if (e.button === 0) { // Left click only
            isPainting = true;
            lastPaintedId = -1;
            viewport.pausePlugin('drag'); // Stop map from panning while we paint
            handleInteraction(e);
        }
    });

    viewport.on('pointerup', () => { isPainting = false; viewport.resumePlugin('drag'); });
    viewport.on('pointerupoutside', () => { isPainting = false; viewport.resumePlugin('drag'); });

    viewport.on('pointermove', (e) => {
        if (isPainting) handleInteraction(e);
    });

    // --- RENDER LOOP ---
    const draw = () => {
        mapGraphics.clear();
        const state = useGameStore.getState();
        if (!state.worldData) return;

        state.worldData.macro_map.forEach((cell: any) => {
            const cx = cell.x;
            const cy = cell.y;

            const size = 12;
            const points: number[] = [];
            for (let a = 0; a < 6; a++) {
                const angle = (Math.PI / 3) * a;
                points.push(cx + size * Math.cos(angle));
                points.push(cy + size * Math.sin(angle));
            }

            // ==========================================
            // LENS 1: PHYSICAL (Biomes & Elevation)
            // ==========================================
            if (state.viewLens === 'PHYSICAL') {
                let color = getBiomeColor(cell.biome_tag, cell.elevation);

                // Add shading for mountains so terrain pops
                if (cell.elevation > 0.8) color = 0xd4d4d8; // Snowcap
                else if (cell.elevation > 0.6) color = 0x52525b; // Dark Grey Rock

                mapGraphics.beginFill(color);
                mapGraphics.drawPolygon(points);
                mapGraphics.endFill();
            }

            // ==========================================
            // LENS 2: POLITICAL (Factions & Borders)
            // ==========================================
            else if (state.viewLens === 'POLITICAL') {
                // Oceans are black, Land is dark grey, Owned land is colored
                let color = cell.elevation <= 0.2 ? 0x050505 : 0x1f1f22;
                if (cell.faction_owner === 'The_Rot_Coven') color = 0x7f1d1d; // Dark Red
                if (cell.faction_owner === 'Iron_Empire') color = 0x1e3a8a; // Dark Blue

                mapGraphics.beginFill(color);
                mapGraphics.drawPolygon(points);
                mapGraphics.endFill();
            }

            // ==========================================
            // LENS 3: RESOURCE (Economy Map)
            // ==========================================
            else if (state.viewLens === 'RESOURCE') {
                mapGraphics.beginFill(0x09090b); // Pitch black map
                mapGraphics.lineStyle(1, 0x27272a, 0.5); // Faint hex borders
                mapGraphics.drawPolygon(points);
                mapGraphics.endFill();

                // Draw bright icons for resources
                if (cell.local_resources?.includes('Iron_Ore')) {
                    mapGraphics.beginFill(0xf97316); // Orange Dot
                    mapGraphics.drawCircle(cx, cy, 4);
                    mapGraphics.endFill();
                }
                if (cell.local_flora?.includes('D-Dust_Spores')) {
                    mapGraphics.beginFill(0x22c55e); // Neon Green Dot
                    mapGraphics.drawCircle(cx - 3, cy + 3, 3);
                    mapGraphics.endFill();
                }
            }

            // ==========================================
            // LENS 4: THREAT (Danger Heatmap)
            // ==========================================
            else if (state.viewLens === 'THREAT') {
                let heatColor = 0x3b82f6; // Safe (Level 1)
                if (cell.threat_level === 2) heatColor = 0xeab308; // Warning
                if (cell.threat_level === 3) heatColor = 0xf97316; // Dangerous
                if (cell.threat_level >= 4) heatColor = 0xef4444; // Lethal

                mapGraphics.beginFill(cell.elevation <= 0.2 ? 0x050505 : heatColor);
                mapGraphics.drawPolygon(points);
                mapGraphics.endFill();
            }

            // --- GLOBAL OVERLAYS ---
            // Always draw City dots no matter what lens is active
            if (cell.is_city) {
                mapGraphics.beginFill(0xffffff);
                mapGraphics.lineStyle(1, 0x000000, 1);
                mapGraphics.drawCircle(cx, cy, 4);
                mapGraphics.endFill();
            }
        });
    };

    // Subscribe to Zustand so map re-draws the instant you paint a hex
    const unsubscribe = useGameStore.subscribe((state, prevState) => {
        if (state.worldData !== prevState.worldData) {
            draw();
        }
    });

    // Initial Draw
    draw();

    return () => {
        unsubscribe();
        app.destroy(true, { children: true });
    };
}, [setSelectedHex, editHex]); // Include new dependencies

return <div ref={containerRef} className="w-full h-full" />;
};
