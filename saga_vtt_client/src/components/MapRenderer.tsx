import React, { useEffect, useRef } from 'react';
import * as PIXI from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import { useGameStore } from '../store/useGameStore';

export const MapRenderer: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<PIXI.Application | null>(null);

    const paintHex = useGameStore((state) => state.paintHex);
    const setSelectedHex = useGameStore((state) => state.setSelectedHex);

    const getBiomeColor = (biome: string, elevation: number) => {
        // Deep water is very dark blue, shallow coastal water is bright teal
        if (elevation <= 0.2) return elevation < 0.1 ? 0x0f172a : 0x0284c7;

        switch (biome) {
            case 'DEEP_TUNDRA': return 0xf1f5f9; // Bright white snow
            case 'SCORCHED_DESERT': return 0xfde047; // Vibrant gold sand
            case 'LUSH_JUNGLE': return 0x166534; // Deep vibrant green
            case 'MUSHROOM_SWAMP': return 0x9333ea; // Bright toxic purple
            case 'OCEAN': return 0x0284c7; // Teal
            default: return 0x4ade80; // Bright green plains fallback instead of grey
        }
    };

    useEffect(() => {
        if (!containerRef.current) return;
        const app = new PIXI.Application();

        app.init({
            background: 0x050505,
            resizeTo: containerRef.current,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true,
        }).then(() => {
            containerRef.current?.appendChild(app.canvas as unknown as HTMLElement);
            appRef.current = app;

            const viewport = new Viewport({
                screenWidth: containerRef.current!.clientWidth,
                screenHeight: containerRef.current!.clientHeight,
                worldWidth: 2000, worldHeight: 2000,
                events: app.renderer.events
            });
            app.stage.addChild(viewport);
            viewport.drag().pinch().wheel().decelerate();

            const mapGraphics = new PIXI.Graphics();
            viewport.addChild(mapGraphics);

            // DRAG PAINTING MATH
            let isPainting = false;
            let lastPaintedId = -1;
            viewport.eventMode = 'static';
            viewport.hitArea = new PIXI.Rectangle(-5000, -5000, 10000, 10000);

            const handleInteraction = (e: any) => {
                const state = useGameStore.getState();
                if (!state.worldData) return;
                const localPos = viewport.toLocal(e.global);
                let minDist = Infinity;
                let nearestId = -1;

                for (let i = 0; i < state.worldData.macro_map.length; i++) {
                    const cell = state.worldData.macro_map[i];
                    const dx = cell.x - localPos.x;
                    const dy = cell.y - localPos.y;
                    const dist = dx * dx + dy * dy;
                    if (dist < minDist) { minDist = dist; nearestId = i; }
                }

                if (nearestId !== -1) {
                    if (state.editMode === 'NONE') {
                        setSelectedHex(state.worldData.macro_map[nearestId]);
                    } else if (isPainting && nearestId !== lastPaintedId && state.activeBrush !== '') {
                        lastPaintedId = nearestId;
                        paintHex(nearestId);
                    }
                }
            };

            viewport.on('pointerdown', (e) => {
                if (e.button === 0) {
                    isPainting = true;
                    lastPaintedId = -1;
                    (viewport.plugins as any).pause('drag');
                    handleInteraction(e);
                }
            });
            viewport.on('pointerup', () => { isPainting = false; (viewport.plugins as any).resume('drag'); });
            viewport.on('pointerupoutside', () => { isPainting = false; (viewport.plugins as any).resume('drag'); });
            viewport.on('pointermove', (e) => { if (isPainting) handleInteraction(e); });

            const draw = () => {
                mapGraphics.clear();
                const state = useGameStore.getState();
                if (!state.worldData) return;

                state.worldData.macro_map.forEach((cell: any) => {
                    const cx = cell.x || 0;
                    const cy = cell.y || 0;

                    // Slightly overdraw the hex size (19 vs 18 spacing) to guarantee overlapping fusion and eliminate 1-pixel grid gaps
                    const size = 19;
                    const points: number[] = [];
                    // Flat-topped hexes 
                    for (let a = 0; a < 6; a++) {
                        const angle = (Math.PI / 3) * a + Math.PI / 6;
                        points.push(cx + size * Math.cos(angle));
                        points.push(cy + size * Math.sin(angle));
                    }

                    if (state.viewLens === 'PHYSICAL') {
                        let color = getBiomeColor(cell.biome_tag, cell.elevation);

                        // Paint the terrain. No black borders on normal land to create smooth rolling continents.
                        mapGraphics.fill(color);
                        mapGraphics.poly(points);
                        mapGraphics.fill();

                        // Only add soft white snowy highlights to extreme elevations
                        if (cell.elevation > 0.8) {
                            mapGraphics.stroke({ width: 2, color: 0xFFFFFF, alpha: 0.3 });
                        }
                    }
                    else if (state.viewLens === 'POLITICAL') {
                        let color = cell.elevation <= 0.2 ? 0x050505 : 0x1f1f22;
                        if (cell.faction_owner === 'The_Rot_Coven') color = 0x7f1d1d;
                        if (cell.faction_owner === 'Iron_Empire') color = 0x1e3a8a;
                        mapGraphics.fill(color);
                        mapGraphics.poly(points);
                        mapGraphics.fill();
                    }
                    else if (state.viewLens === 'RESOURCE') {
                        mapGraphics.fill(0x09090b);
                        mapGraphics.poly(points);
                        mapGraphics.stroke({ width: 1, color: 0x27272a, alpha: 0.5 });
                        mapGraphics.fill();

                        if (cell.local_resources?.includes('Iron_Ore')) {
                            mapGraphics.fill(0xf97316); mapGraphics.circle(cx, cy, 4); mapGraphics.fill();
                        }
                        if (cell.local_flora?.includes('D-Dust_Spores')) {
                            mapGraphics.fill(0x22c55e); mapGraphics.circle(cx - 3, cy + 3, 3); mapGraphics.fill();
                        }
                    }
                    else if (state.viewLens === 'THREAT') {
                        let heatColor = 0x3b82f6;
                        if (cell.threat_level === 2) heatColor = 0xeab308;
                        if (cell.threat_level === 3) heatColor = 0xf97316;
                        if (cell.threat_level >= 4) heatColor = 0xef4444;
                        mapGraphics.fill(cell.elevation <= 0.2 ? 0x050505 : heatColor);
                        mapGraphics.poly(points);
                        mapGraphics.fill();
                    }

                    if (cell.is_city) {
                        mapGraphics.fill(0xffffff);
                        mapGraphics.circle(cx, cy, 4);
                        mapGraphics.stroke({ width: 1, color: 0x000000, alpha: 1 });
                        mapGraphics.fill();
                    }
                });
            };

            const unsubscribe = useGameStore.subscribe((state, prevState) => {
                if (state.worldData !== prevState.worldData || state.viewLens !== prevState.viewLens) {
                    draw();
                }
            });
            draw(); // initial draw

            // CLEANUP EVENT LISTENERS ON UNMOUNT
            return () => {
                unsubscribe();
                app.destroy(true, { children: true });
            };
        });

    }, [paintHex, setSelectedHex]);

    return <div ref={containerRef} className="w-full h-full" />;
};
