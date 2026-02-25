import { useEffect, useRef, useCallback } from 'react';
import { Application, Graphics, Text, TextStyle, Container } from 'pixi.js';
import { useGameStore } from '../../store/useGameStore';

const TILE_SIZE = 64;
const GRID_COLS = 16;
const GRID_ROWS = 10;

export function PixiBattlemap() {
    const containerRef = useRef<HTMLDivElement>(null);
    const appRef = useRef<Application | null>(null);
    const mapTokens = useGameStore((s) => s.map_tokens);
    const selectedTokenId = useGameStore((s) => s.selectedTokenId);
    const selectToken = useGameStore((s) => s.selectToken);

    const draw = useCallback(() => {
        const app = appRef.current;
        if (!app) return;

        // Clear previous children
        while (app.stage.children.length > 0) {
            app.stage.removeChildAt(0);
        }

        // Draw checkerboard grid
        const gridContainer = new Container();
        for (let row = 0; row < GRID_ROWS; row++) {
            for (let col = 0; col < GRID_COLS; col++) {
                const tile = new Graphics();
                const isLight = (row + col) % 2 === 0;
                tile.rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                tile.fill(isLight ? 0x1c1c1c : 0x171717);
                tile.rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                tile.stroke({ width: 1, color: 0x2a2a2a });
                gridContainer.addChild(tile);
            }
        }
        app.stage.addChild(gridContainer);

        // Draw tokens
        const tokenContainer = new Container();
        mapTokens.forEach((token) => {
            const tokenGroup = new Container();
            tokenGroup.x = token.x * TILE_SIZE;
            tokenGroup.y = token.y * TILE_SIZE;
            tokenGroup.eventMode = 'static';
            tokenGroup.cursor = 'pointer';
            tokenGroup.on('pointerdown', () => {
                selectToken(token.id === selectedTokenId ? null : token.id);
            });

            // Token circle
            const circle = new Graphics();
            const isSelected = token.id === selectedTokenId;

            if (isSelected) {
                // Selection glow ring
                circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 2 - 2);
                circle.fill({ color: token.tint, alpha: 0.15 });
                circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 2 - 2);
                circle.stroke({ width: 3, color: 0xfbbf24 });
            }

            circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
            circle.fill(token.tint);
            circle.circle(TILE_SIZE / 2, TILE_SIZE / 2, TILE_SIZE / 3);
            circle.stroke({ width: 2, color: 0x000000 });

            tokenGroup.addChild(circle);

            // Token label
            const label = new Text({
                text: token.label.charAt(0),
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

            tokenContainer.addChild(tokenGroup);
        });
        app.stage.addChild(tokenContainer);
    }, [mapTokens, selectedTokenId, selectToken]);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;

        let cancelled = false;
        const app = new Application();

        app.init({
            background: 0x0f0f0f,
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
            draw();
        });

        return () => {
            cancelled = true;
            if (appRef.current) {
                appRef.current.destroy(true);
                appRef.current = null;
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
