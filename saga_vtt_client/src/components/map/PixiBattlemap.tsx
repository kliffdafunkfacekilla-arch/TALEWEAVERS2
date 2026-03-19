import { useEffect, useRef, useCallback } from 'react';
import { Application, Graphics, Text, TextStyle, Container, Rectangle, Sprite, Texture, TilingSprite, Assets, Spritesheet } from 'pixi.js';
import { Viewport } from 'pixi-viewport';
import { useCombatStore } from '../../store/useCombatStore';

const TILE_SIZE = 50;

export function PixiBattlemap() {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const cameraRef = useRef<Viewport | null>(null);

    const activeEncounter = useCombatStore((s) => s.activeEncounter);
    const selectedTargetId = useCombatStore((s) => s.selectedTargetId);
    const atlasRef = useRef<Spritesheet | null>(null);

    const draw = useCallback(() => {
        const app = appRef.current;
        const camera = cameraRef.current;
        const atlasSheet = atlasRef.current; // Always reads current atlas, no stale closure
        if (!app || !camera) return;

        while (camera.children.length > 0) {
            camera.removeChildAt(0);
        }

        if (!activeEncounter) return;

        const GRID_W = activeEncounter.gridWidth ?? 15;
        const GRID_H = activeEncounter.gridHeight ?? 10;

        // ── 0. Draw Seamless Biome Background Layer ──
        const mainBiome = (activeEncounter as any).metadata?.biome || activeEncounter.data?.category || "FOREST";

        let bgTexture: Texture | null = null;
        if (atlasSheet) {
            const biomeKeyMap: Record<string, string> = {
                "FOREST": "floor/grass_full_new", "RUINS": "tiles/floor_stone",
                "MOUNTAIN": "floor/floor_sand_rock_0", "SWAMP": "floor/swamp_0_new",
                "TUNDRA": "floor/ice_0_new", "DESERT": "floor/sand_1",
                "DUNGEON": "floor/crypt_10", "AMBIENT": "floor/grass_full_new",
                "Wilderness": "floor/grass_full_new", "Forest": "floor/grass_full_new",
                "Plains": "floor/grass_full_new", "Grassland": "floor/grass_full_new",
                "Swamp": "floor/swamp_0_new", "Mountain": "floor/floor_sand_rock_0",
                "Tundra": "floor/ice_0_new", "Desert": "floor/sand_1",
                "Ruins": "tiles/floor_stone", "Dungeon": "floor/crypt_10",
            };
            const key = biomeKeyMap[mainBiome] || "floor/grass_full_new";
            bgTexture = atlasSheet.textures[key];
        }
        if (bgTexture) {
            const tilingBG = new TilingSprite({ texture: bgTexture, width: GRID_W * TILE_SIZE, height: GRID_H * TILE_SIZE });
            tilingBG.alpha = 0.4;
            camera.addChild(tilingBG);
        }

        // ── 1. Draw Checkerboard Grid & Terrain ──
        const gridGraphics = new Graphics();
        const terrainGrid = activeEncounter.grid || [];

        for (let row = 0; row < GRID_H; row++) {
            for (let col = 0; col < GRID_W; col++) {
                const tileType = (terrainGrid[row] ? terrainGrid[row][col] : "EMPTY") as string;

                // Simple grid lines (textures are behind this)
                gridGraphics.rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                gridGraphics.stroke({ width: 1, color: 0x2a2a2a, alpha: 0.5 });

                // Render Obstacles & Interactive Objects
                if (tileType !== "EMPTY" && atlasSheet) {
                    const objectKeyMap: Record<string, string> = {
                        "TREE": "trees/tree_1_red",
                        "WALL": "tiles/wall_stone",
                        "ROCK": "floor/pebble_brown_0_new",
                        "BARREL": "objects/barrel",
                        "CRATE": "objects/crate",
                        "TABLE": "objects/table",
                        "CHEST": "objects/chest"
                    };

                    const tex = atlasSheet.textures[objectKeyMap[tileType]];
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
            const currentEncounter = useCombatStore.getState().activeEncounter;
            if (!currentEncounter) return;

            const clickedToken = currentEncounter.tokens.find((t: any) => t.x === gridX && t.y === gridY);
            if (clickedToken && !clickedToken.isPlayer) {
                // Target the enemy
                const currentTarget = useCombatStore.getState().selectedTargetId;
                // @ts-ignore
                useCombatStore.getState().setSelectedTarget(clickedToken.id === currentTarget ? null : clickedToken.id);
                return;
            }

            // Move player + clear target
            // @ts-ignore
            useCombatStore.getState().moveToken('PLAYER_001', gridX, gridY);
            // @ts-ignore
            useCombatStore.getState().setSelectedTarget(null);
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

            // ── TOKEN VISUALS (Composite Layers or Stylized Disc) ──
            const tokenContainer = new Container();
            tokenGroup.addChild(tokenContainer);

            if (token.composite_sprite?.layers && token.composite_sprite.layers.length > 0) {
                // Render Layers from bottom to top
                const assetUrl = import.meta.env.VITE_SAGA_ASSET_FOUNDRY_URL || 'http://localhost:8012';
                token.composite_sprite.layers.forEach((layer) => {
                    Assets.load(`${assetUrl}${layer.sheet_url}`).then((tex: Texture) => {
                        const spriteTex = new Texture({
                            source: tex.source,
                            frame: new Rectangle(layer.x, layer.y, layer.w, layer.h)
                        });
                        const sprite = new Sprite(spriteTex);
                        sprite.anchor.set(0.5);
                        sprite.x = TILE_SIZE / 2;
                        sprite.y = TILE_SIZE / 2;
                        sprite.width = TILE_SIZE * 0.9;
                        sprite.height = TILE_SIZE * 0.9;
                        if (layer.tint) sprite.tint = layer.tint;
                        tokenContainer.addChild(sprite);
                    });
                });
            } else if (token.avatar_sprite) {
                const meta = token.avatar_sprite;
                const assetUrl = import.meta.env.VITE_SAGA_ASSET_FOUNDRY_URL || 'http://localhost:8012';
                Assets.load(`${assetUrl}${meta.sheet_url}`).then((tex: Texture) => {
                    const spriteTex = new Texture({
                        source: tex.source,
                        frame: new Rectangle(meta.x, meta.y, meta.w, meta.h)
                    });
                    const sprite = new Sprite(spriteTex);
                    sprite.anchor.set(0.5);
                    sprite.x = TILE_SIZE / 2;
                    sprite.y = TILE_SIZE / 2;
                    sprite.width = TILE_SIZE * 0.9;
                    sprite.height = TILE_SIZE * 0.9;
                    tokenContainer.addChild(sprite);
                });
            } else {
                // Fallback to stylized disc
                const circle = new Graphics();
                const tokenColor = token.color || 0x3B82F6;
                circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
                circle.fill(tokenColor);
                circle.stroke({ width: 2, color: 0x000000 });
                tokenContainer.addChild(circle);

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
                tokenContainer.addChild(label);
            }

            // --- S.A.G.A Visuals: HP, Composure, etc. ---
            const fx = new Graphics();

            // Targeting reticle
            if (isTargeted) {
                fx.rect(2, 2, TILE_SIZE - 4, TILE_SIZE - 4);
                fx.stroke({ width: 3, color: 0xFF0000, alpha: 0.8 });
            }

            // Selection ring for player
            if (token.isPlayer) {
                fx.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 2 - 2);
                fx.stroke({ width: 2, color: 0x3B82F6, alpha: 0.6 });
            }
            tokenGroup.addChild(fx);

            // 1. Directional Indicator
            const dir = token.direction || 0;
            const indicator = new Graphics();
            indicator.poly([-6, 0, 6, 0, 0, -10]);
            indicator.fill(0xffffff);
            indicator.x = TILE_SIZE / 2;
            indicator.y = TILE_SIZE / 2;
            indicator.rotation = (dir * Math.PI) / 2;
            tokenGroup.addChild(indicator);

            // 2. Health & Composure Bars
            const bars = new Graphics();
            const barW = TILE_SIZE - 10;
            const healthPercent = (token as any).current_hp / ((token as any).max_hp || 10);
            bars.rect(5, TILE_SIZE - 8, barW, 3);
            bars.fill(0x333333);
            bars.rect(5, TILE_SIZE - 8, barW * healthPercent, 3);
            bars.fill(0x22c55e);
            tokenGroup.addChild(bars);

            // 3. Prone indicator
            if (token.is_prone) {
                tokenContainer.alpha = 0.5;
                const proneText = new Text({ text: "PRONE", style: { fontSize: 8, fill: 0xff4444, fontWeight: 'bold' } });
                proneText.anchor.set(0.5);
                proneText.x = TILE_SIZE / 2;
                proneText.y = TILE_SIZE / 2 + 10;
                tokenGroup.addChild(proneText);
            }

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

        // Center on player if present
        const playerToken = activeEncounter.tokens?.find((t: any) => t.isPlayer);
        if (playerToken) {
            const px = playerToken.x * TILE_SIZE + TILE_SIZE / 2;
            const py = playerToken.y * TILE_SIZE + TILE_SIZE / 2;
            camera.moveCenter(px, py);
        } else {
            camera.moveCenter((GRID_W * TILE_SIZE) / 2, (GRID_H * TILE_SIZE) / 2);
        }
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
            if (cancelled) { app.destroy(true); return; }

            // Set up canvas and viewport FIRST so draw() can fire at any time
            el.appendChild(app.canvas as HTMLCanvasElement);
            appRef.current = app;

            const viewport = new Viewport({
                screenWidth: el.clientWidth,
                screenHeight: el.clientHeight,
                worldWidth: 5000,
                worldHeight: 5000,
                events: app.renderer.events
            });
            app.stage.addChild(viewport);
            viewport.drag().pinch().wheel().decelerate();
            cameraRef.current = viewport;

            // Draw immediately with whatever encounter data exists (grid without textures)
            draw();

            // Load Individual Textures instead of Mega-Atlas (Bypasses decoding limits)
            try {
                const assetUrl = import.meta.env.VITE_SAGA_ASSET_FOUNDRY_URL || 'http://localhost:8012';

                // Load common biome textures individually
                const biomeKeys = ["floor/grass_full_new", "tiles/floor_stone", "floor/floor_sand_rock_0", "floor/swamp_0_new", "floor/ice_0_new", "floor/sand_1", "floor/crypt_10"];
                const objectKeys = ["trees/tree_1_red", "tiles/wall_stone", "floor/pebble_brown_0_new", "objects/barrel", "objects/crate", "objects/table", "objects/chest"];

                const texturePromises = [...biomeKeys, ...objectKeys].map(async (key) => {
                    try {
                        const tex = await Assets.load(`${assetUrl}/public/${key}.png`);
                        return { key, tex };
                    } catch (e) {
                        console.warn(`[PixiBattlemap] Failed to load individual texture: ${key}`, e);
                        return { key, tex: null };
                    }
                });

                const results = await Promise.all(texturePromises);
                const textures: Record<string, Texture> = {};
                results.forEach(res => {
                    if (res.tex) textures[res.key] = res.tex;
                });

                if (!cancelled) {
                    // Create a mock spritesheet object for compatibility with drawing logic
                    atlasRef.current = { textures } as any;
                    draw();
                }
            } catch (e) {
                console.warn("[PixiBattlemap] Failed to load individual textures.", e);
            }
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
