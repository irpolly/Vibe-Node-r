import { useEffect, useRef } from 'react';

interface EmulatorProps {
  gameCode: string;
}

export default function Emulator({ gameCode }: EmulatorProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const gameRef = useRef<Phaser.Game | null>(null);

  // === AUTO-FIX: Ensure index.html has game-container ===
  useEffect(() => {
    const container = document.getElementById('game-container');
    if (!container) {
      const div = document.createElement('div');
      div.id = 'game-container';
      document.getElementById('emulator-container')?.appendChild(div);
    }
  }, []);

  // === ASSET PACKER: Inline all assets ===
  const packAssets = (scene: Phaser.Scene) => {
    scene.load.on('filecomplete', (file: any) => {
      if (file.type === 'image') {
        const img = scene.textures.get(file.key).getSourceImage() as HTMLImageElement;
        window.__ASSET_PACK = window.__ASSET_PACK || {};
        window.__ASSET_PACK[file.key] = img.src;
      }
      if (file.type === 'audio') {
        const sound = scene.sound.get(file.key);
        if (sound) window.__ASSET_PACK[file.key] = sound.config.src[0];
      }
    });
  };

  // === RUN GAME ===
  useEffect(() => {
    if (!containerRef.current || !gameCode) return;

    // Clean up old game
    gameRef.current?.destroy(true);
    const container = document.getElementById('game-container');
    if (!container) return;

    // Inject Phaser if missing
    if (!window.Phaser) {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js';
      document.head.appendChild(script);
      script.onload = () => runGame();
    } else {
      runGame();
    }

    function runGame() {
      try {
        const func = new Function('Phaser', 'container', gameCode + '; return config;');
        const config = func(window.Phaser, container);
        config.parent = 'game-container';
        config.scene = config.scene || [];

        // Inject BootScene with asset packing
        config.scene.unshift(class extends Phaser.Scene {
          constructor() { super('AutoBoot'); }
          preload() { packAssets(this); }
          create() { this.scene.start(config.scene[1] || 'PlayScene'); }
        });

        gameRef.current = new window.Phaser.Game(config);
      } catch (err) {
        document.getElementById('manager-feed')!.innerHTML += `<br>> [FIX] ${err}`;
      }
    }

    return () => { gameRef.current?.destroy(true); };
  }, [gameCode]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
}