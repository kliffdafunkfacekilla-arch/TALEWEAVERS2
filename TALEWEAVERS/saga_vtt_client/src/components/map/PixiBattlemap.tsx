import { useEffect, useRef, useCallback } from 'react';
import { Application, Graphics, Text, TextStyle, Container, Rectangle } from 'pixi.js';
import { useGameStore } from '../../store/useGameStore';

const TILE_SIZE = 50;

export function PixiBattlemap() {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const cameraRef = useRef<Container | null>(null);

    const activeEncounter = useGameStore((s) => s.activeEncounter);
    const selectedTargetId = useGameStore((s) => s.selectedTargetId);

    // ── REAL ENCOUNTER FETCH (PORT 8004) ──
    useEffect(() => {
        const fetchRealEncounter = async () => {
            // Only fetch if we don't already have an active encounter
            if (activeEncounter) return;

            try {
                // Read the current biome from the selected hex, or use a default
                const currentBiome = useGameStore.getState().selectedHex?.biome_tag || "Tundra";

                console.log(`[VTT] Requesting encounter for biome: ${currentBiome}`);
                const res = await fetch(`http://localhost:8004/generate-encounter?biome=${currentBiome}&threat_level=4`);

                if (!res.ok) throw new Error("Encounter Engine offline.");
                const data = await res.json();

                // Always spawn the Player Token
                const dynamicTokens = [
                    { id: 'player_1', name: 'Scavenger', x: 2, y: 5, color: 0x3B82F6, isPlayer: true }
                ];

                // If this is a COMBAT encounter, spawn enemy tokens from the response
                if (data.type === "COMBAT" && data.enemies && Array.isArray(data.enemies)) {
                    data.enemies.forEach((enemy: any, index: number) => {
                        dynamicTokens.push({
                            id: `enemy_${index}`,
                            name: enemy.name,
                            x: 8 + (index * 2),
                            y: 3 + index,
                            color: 0xEF4444,
                            isPlayer: false
                        });
                    });
                }

                // Save to Zustand
                useGameStore.getState().setActiveEncounter({
                    gridWidth: 15,
                    gridHeight: 10,
                    tokens: dynamicTokens
                });

                // Post encounter description to Director Log
                useGameStore.getState().addChatMessage({
                    sender: 'SYSTEM',
                    text: `ENCOUNTER: ${data.name}. ${data.description}`
                });

                console.log(`[VTT] Encounter loaded: ${data.name} (${data.type})`);

            } catch (err) {
                console.warn("Encounter Engine (Port 8004) unavailable. Loading fallback.", err);

                // Fallback: spawn a basic encounter without the server
                useGameStore.getState().setActiveEncounter({
                    gridWidth: 15,
                    gridHeight: 10,
                    tokens: [
                        { id: 'player_1', name: 'Scavenger', x: 2, y: 5, color: 0x3B82F6, isPlayer: true },
                        { id: 'enemy_1', name: 'Unknown Entity', x: 8, y: 5, color: 0xEF4444, isPlayer: false }
                    ]
                });
            }
        };

        fetchRealEncounter();
    }, [activeEncounter]);

    const draw = useCallback(() => {
        const app = appRef.current;
        const camera = cameraRef.current;
        if (!app || !camera || !activeEncounter) return;

        // Clear previous children
        while (camera.children.length > 0) {
            camera.removeChildAt(0);
        }

        const GRID_W = activeEncounter.gridWidth;
        const GRID_H = activeEncounter.gridHeight;

        // ── 1. Draw Checkerboard Grid ──
        const gridGraphics = new Graphics();
        for (let row = 0; row < GRID_H; row++) {
            for (let col = 0; col < GRID_W; col++) {
                const isLight = (row + col) % 2 === 0;
                gridGraphics.rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                gridGraphics.fill(isLight ? 0x1c1c1c : 0x171717);
                gridGraphics.rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                gridGraphics.stroke({ width: 1, color: 0x2a2a2a });
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
                const currentTarget = useGameStore.getState().selectedTargetId;
                useGameStore.getState().setTarget(clickedToken.id === currentTarget ? null : clickedToken.id);
                console.log(`[VTT] Targeted: ${clickedToken.name} at [${gridX}, ${gridY}]`);
                return;
            }

            // Move player + clear target
            useGameStore.getState().moveToken('player_1', gridX, gridY);
            useGameStore.getState().setTarget(null);
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
            circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
            circle.fill(token.color);
            circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
            circle.stroke({ width: 2, color: 0x000000 });
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
