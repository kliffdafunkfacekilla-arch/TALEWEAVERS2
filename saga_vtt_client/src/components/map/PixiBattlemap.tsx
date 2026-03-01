import { useEffect, useRef, useCallback } from 'react';
import { Application, Graphics, Text, TextStyle, Container, Rectangle } from 'pixi.js';
import { useGameStore } from '../../store/useGameStore';
import { useCombatStore } from '../../store/useCombatStore';

const TILE_SIZE = 50;

export function PixiBattlemap() {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const cameraRef = useRef<Container | null>(null);

    const activeEncounter = useCombatStore((s) => s.activeEncounter);
    const selectedTargetId = useCombatStore((s) => s.selectedTargetId);

    // ── REMOVED: Redundant Direct Fetch ──
    // Encounters are now managed by the Game Master (Port 8000) 
    // to ensure naration and mechanics are synced.
    useEffect(() => {
        // If we want a default empty map if no encounter is active, we can handle it here.
        // But we don't fetch from Port 8009 directly anymore.
    }, [activeEncounter]);

    const draw = useCallback(() => {
        const app = appRef.current;
        const camera = cameraRef.current;
        if (!app || !camera) return;

        // Clear previous children
        while (camera.children.length > 0) {
            camera.removeChildAt(0);
        }

        if (!activeEncounter) return;

        const GRID_W = activeEncounter.gridWidth ?? 15;
        const GRID_H = activeEncounter.gridHeight ?? 10;

        // ── 1. Draw Checkerboard Grid & Terrain ──
        const gridGraphics = new Graphics();
        const terrainGrid = activeEncounter.grid || [];

        for (let row = 0; row < GRID_H; row++) {
            for (let col = 0; col < GRID_W; col++) {
                const isLight = (row + col) % 2 === 0;
                const tileType = (terrainGrid[row] ? terrainGrid[row][col] : "EMPTY") as string;

                // Base Tile Color
                let bgColor = isLight ? 0x1c1c1c : 0x171717;
                if (tileType === "SNOW") bgColor = isLight ? 0xe0e0e0 : 0xd0d0d0;
                if (tileType === "SAND_DUNES") bgColor = isLight ? 0xd4a373 : 0xbc8a5f;
                if (tileType === "WATER") bgColor = 0x2244aa;

                gridGraphics.rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                gridGraphics.fill(bgColor);
                gridGraphics.rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                gridGraphics.stroke({ width: 1, color: 0x2a2a2a });

                // Render Obstacles
                if (tileType === "TREE") {
                    gridGraphics.circle(col * TILE_SIZE + TILE_SIZE / 2, row * TILE_SIZE + TILE_SIZE / 2, TILE_SIZE / 3);
                    gridGraphics.fill({ color: 0x064e3b, alpha: 0.8 });
                    gridGraphics.circle(col * TILE_SIZE + TILE_SIZE / 2, row * TILE_SIZE + TILE_SIZE / 2, TILE_SIZE / 3);
                    gridGraphics.stroke({ width: 2, color: 0x022c22 });
                } else if (tileType === "ROCK") {
                    gridGraphics.poly([
                        col * TILE_SIZE + 10, row * TILE_SIZE + 10,
                        col * TILE_SIZE + 40, row * TILE_SIZE + 15,
                        col * TILE_SIZE + 35, row * TILE_SIZE + 40,
                        col * TILE_SIZE + 15, row * TILE_SIZE + 35
                    ]);
                    gridGraphics.fill({ color: 0x4b5563, alpha: 0.9 });
                }
            }
        }

        // ── Grid Click: Move Player Token + Clear Target ──
        gridGraphics.eventMode = 'static';
        gridGraphics.hitArea = new Rectangle(0, 0, GRID_W * TILE_SIZE, GRID_H * TILE_SIZE);
        gridGraphics.cursor = 'crosshair';

        gridGraphics.on('pointerdown', (e) => {
            const localPos = gridGraphics.toLocal(e.global);
            const gridX = Math.floor(localPos.x / TILE_SIZE);
            const gridY = Math.floor(localPos.y / TILE_SIZE);
            if (gridX < 0 || gridX >= GRID_W || gridY < 0 || gridY >= GRID_H) return;

            // Check if clicking on an enemy token → target it
            const currentEncounter = useGameStore.getState().activeEncounter;
            if (!currentEncounter) return;

            const clickedToken = currentEncounter.tokens.find(t => t.x === gridX && t.y === gridY);
            if (clickedToken && !clickedToken.isPlayer) {
                // Target the enemy
                const currentTarget = useCombatStore.getState().selectedTargetId;
                useCombatStore.getState().setSelectedTarget(clickedToken.id === currentTarget ? null : clickedToken.id);
                console.log(`[VTT] Targeted: ${clickedToken.name} at [${gridX}, ${gridY}]`);
                return;
            }

            // Move player + clear target
            useCombatStore.getState().moveToken('PLAYER_001', gridX, gridY);
            useCombatStore.getState().setSelectedTarget(null);
            console.log(`[VTT] Player moved to Grid [${gridX}, ${gridY}]`);
        });

        camera.addChild(gridGraphics);

        // ── 2. Draw Tokens ──
        let playerCenterX = 0;
        let playerCenterY = 0;
        let targetCenterX = 0;
        let targetCenterY = 0;

        activeEncounter.tokens.forEach((token) => {
            const tokenGroup = new Container();
            tokenGroup.x = token.x * TILE_SIZE;
            tokenGroup.y = token.y * TILE_SIZE;

            const centerX = tokenGroup.x + TILE_SIZE / 2;
            const centerY = tokenGroup.y + TILE_SIZE / 2;

            if (token.isPlayer) {
                playerCenterX = centerX;
                playerCenterY = centerY;
            }

            const isTargeted = token.id === selectedTargetId;
            if (isTargeted) {
                targetCenterX = centerX;
                targetCenterY = centerY;
            }

            const circle = new Graphics();

            // Targeting reticle (red square around targeted enemy)
            if (isTargeted) {
                circle.rect(2, 2, TILE_SIZE - 4, TILE_SIZE - 4);
                circle.stroke({ width: 3, color: 0xFF0000, alpha: 0.8 });
            }

            // Selection ring for player
            if (token.isPlayer) {
                circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 2 - 2);
                circle.fill({ color: token.color, alpha: 0.1 });
                circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 2 - 2);
                circle.stroke({ width: 2, color: 0x3B82F6, alpha: 0.6 });
            }

            // Token body
            const tokenColor = (token as any).color || (token as any).tint || 0x3B82F6;
            circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
            circle.fill(tokenColor);
            circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
            circle.stroke({ width: 2, color: 0x000000 });

            // --- S.A.G.A Visuals: Orientation, HP, Composure ---
            // 1. Directional Indicator (Triangle pointing Front)
            const dir = token.direction || 0; // 0=N, 1=E, 2=S, 3=W
            const indicator = new Graphics();
            indicator.poly([-6, 0, 6, 0, 0, -10]);
            indicator.fill(0xffffff);
            indicator.x = TILE_SIZE / 2;
            indicator.y = TILE_SIZE / 2;
            indicator.rotation = (dir * Math.PI) / 2;
            tokenGroup.addChild(indicator);

            // 2. Health & Composure Bars (Small bars below token)
            const bars = new Graphics();
            const barW = TILE_SIZE - 10;
            // HP Bar (Green)
            bars.rect(5, TILE_SIZE - 8, barW, 3);
            bars.fill(0x333333);
            bars.rect(5, TILE_SIZE - 8, barW * 0.7, 3); // 70% fill for demo
            bars.fill(0x22c55e);
            // Composure Bar (Purple/Blue)
            bars.rect(5, TILE_SIZE - 4, barW, 2);
            bars.fill(0x333333);
            bars.rect(5, TILE_SIZE - 4, barW * 0.8, 2);
            bars.fill(0x8b5cf6);
            tokenGroup.addChild(bars);

            // 3. Prone indicator
            if (token.is_prone) {
                circle.alpha = 0.5;
                const proneText = new Text({ text: "PRONE", style: { fontSize: 8, fill: 0xff4444, fontWeight: 'bold' } });
                proneText.anchor.set(0.5);
                proneText.x = TILE_SIZE / 2;
                proneText.y = TILE_SIZE / 2 + 10;
                tokenGroup.addChild(proneText);
            }

            tokenGroup.addChild(circle);

            // Token initial letter
            const label = new Text({
                text: token.name.charAt(0),
                style: new TextStyle({
                    fontFamily: 'Inter, sans-serif',
                    fontSize: 18,
                    fontWeight: 'bold',
                    fill: 0xffffff,
                }),
            });
            label.anchor.set(0.5);
            label.x = TILE_SIZE / 2;
            label.y = TILE_SIZE / 2;
            tokenGroup.addChild(label);

            // Token name label below
            const nameLabel = new Text({
                text: token.name,
                style: new TextStyle({
                    fontFamily: 'monospace',
                    fontSize: 9,
                    fill: isTargeted ? 0xff6666 : 0xaaaaaa,
                    align: 'center',
                }),
            });
            nameLabel.anchor.set(0.5);
            nameLabel.x = TILE_SIZE / 2;
            nameLabel.y = TILE_SIZE + 4;
            tokenGroup.addChild(nameLabel);

            camera.addChild(tokenGroup);
        });

        // ── 3. Laser Sight Line (player → target) ──
        if (selectedTargetId) {
            const laserLine = new Graphics();
            laserLine.moveTo(playerCenterX, playerCenterY);
            laserLine.lineTo(targetCenterX, targetCenterY);
            laserLine.stroke({ width: 2, color: 0xFF0000, alpha: 0.4 });

            // Distance label at midpoint
            const player = activeEncounter.tokens.find(t => t.isPlayer);
            const target = activeEncounter.tokens.find(t => t.id === selectedTargetId);
            if (player && target) {
                const dist = Math.max(Math.abs(player.x - target.x), Math.abs(player.y - target.y));
                const midX = (playerCenterX + targetCenterX) / 2;
                const midY = (playerCenterY + targetCenterY) / 2;

                const distLabel = new Text({
                    text: `${dist} sq`,
                    style: new TextStyle({
                        fontFamily: 'monospace',
                        fontSize: 11,
                        fontWeight: 'bold',
                        fill: 0xFF4444,
                    }),
                });
                distLabel.anchor.set(0.5);
                distLabel.x = midX;
                distLabel.y = midY - 10;
                camera.addChild(distLabel);
            }

            camera.addChild(laserLine);
        }

        // Center grid in view
        camera.x = (app.screen.width - (GRID_W * TILE_SIZE)) / 2;
        camera.y = (app.screen.height - (GRID_H * TILE_SIZE)) / 2;

    }, [activeEncounter, selectedTargetId]);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        let cancelled = false;
        const app = new Application();

        app.init({
            background: 0x0a0a0a,
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

            const camera = new Container();
            app.stage.addChild(camera);
            cameraRef.current = camera;

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
            className="w-full h-full shadow-[inset_0_0_50px_rgba(0,0,0,0.8)]"
            style={{ touchAction: 'none' }}
        />
    );
}
