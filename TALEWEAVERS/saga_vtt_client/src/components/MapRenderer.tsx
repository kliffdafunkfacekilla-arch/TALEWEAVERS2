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

        worldData.macro_map.forEach((cell: HexCell) => {
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
                appRef.current = null;
                cameraRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        draw();
    }, [draw]);

    return (
        <div
            ref={containerRef}
            className="w-full h-full"
            style={{ touchAction: 'none' }}
        />
    );
}
