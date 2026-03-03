import { useEffect, useRef, useCallback, useState } from 'react';
import { Application, Graphics, Text, TextStyle, Container, Rectangle, Sprite, Texture, TilingSprite, Assets, Spritesheet } from 'pixi.js';
import { useGameStore } from '../../store/useGameStore';
import { useCombatStore } from '../../store/useCombatStore';

const TILE_SIZE = 50;

export function PixiBattlemap() {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const cameraRef = useRef<Container | null>(null);

    const activeEncounter = useCombatStore((s) => s.activeEncounter);
    const selectedTargetId = useCombatStore((s) => s.selectedTargetId);
    const [atlas, setAtlas] = useState<Spritesheet | null>(null);

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

        // ── 0. Draw Seamless Biome Background Layer ──
        const mainBiome = activeEncounter.data?.category === "COMBAT" ? (activeEncounter as any).biome || "FOREST" : "FOREST";

        let bgTexture: Texture | null = null;
        if (atlas) {
            const biomeKeyMap: Record<string, string> = {
                "FOREST": "floor/grass_full_new",
                "RUINS": "tiles/floor_stone",
                "MOUNTAIN": "floor/floor_sand_rock_0",
                "SWAMP": "floor/swamp_0_new",
                "TUNDRA": "floor/ice_0_new",
                "DESERT": "floor/sand_1",
                "DUNGEON": "floor/crypt_10"
            };
            const key = biomeKeyMap[mainBiome] || "floor/grass_0_new";
            bgTexture = atlas.textures[key];
        }

        if (bgTexture) {
            const tilingBG = new TilingSprite({
                texture: bgTexture,
                width: GRID_W * TILE_SIZE,
                height: GRID_H * TILE_SIZE,
            });
            tilingBG.alpha = 0.4;
            camera.addChild(tilingBG);
        }

        // ── 1. Draw Checkerboard Grid & Terrain ──
        const gridGraphics = new Graphics();
        const terrainGrid = activeEncounter.grid || [];

        for (let row = 0; row < GRID_H; row++) {
            for (let col = 0; col < GRID_W; col++) {
                const isLight = (row + col) % 2 === 0;
                const tileType = (terrainGrid[row] ? terrainGrid[row][col] : "EMPTY") as string;

                // Simple grid lines (textures are behind this)
                gridGraphics.rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                gridGraphics.stroke({ width: 1, color: 0x2a2a2a, alpha: 0.5 });

                // Render Obstacles & Interactive Objects
                if (tileType !== "EMPTY" && atlas) {
                    const objectKeyMap: Record<string, string> = {
                        "TREE": "trees/tree_1_red",
                        "WALL": "tiles/wall_stone",
                        "ROCK": "floor/pebble_brown_0_new",
                        "BARREL": "objects/barrel",
                        "CRATE": "objects/crate",
                        "TABLE": "objects/table",
                        "CHEST": "objects/chest"
                    };

                    const tex = atlas.textures[objectKeyMap[tileType]];
                    if (tex) {
                        const sprite = new Sprite(tex);
                        sprite.anchor.set(0.5);
                        sprite.x = col * TILE_SIZE + TILE_SIZE / 2;
                        sprite.y = row * TILE_SIZE + TILE_SIZE / 2;

                        // Objects slightly smaller than the tile to show floor under them
                        const scaleFactor = ["BARREL", "CRATE", "CHEST", "TABLE"].includes(tileType) ? 0.7 : 0.9;
                        sprite.width = TILE_SIZE * scaleFactor;
                        sprite.height = TILE_SIZE * scaleFactor;

                        camera.addChild(sprite);
                    }
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
        }).then(async () => {
            if (cancelled) {
                app.destroy(true);
                return;
            }

            // Load Texture Atlas
            try {
                const sheet = await Assets.load('http://localhost:8012/public/../assets/atlas.json');
                if (!cancelled) setAtlas(sheet);
            } catch (e) {
                console.error("Failed to load texture atlas:", e);
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
