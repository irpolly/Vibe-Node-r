
import React, { useRef, useEffect } from 'react';

const MatrixBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const columns = Math.floor(width / 20);
    const drops: number[] = [];
    for (let i = 0; i < columns; i++) {
      drops[i] = 1;
    }

    const characters = '的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下';
    const specialWord = 'VibeNoder';
    const specialWordColor = '#FF0000'; // Red
    const defaultColor = '#800020'; // Burgundy

    let wordColumn = -1;
    let wordY = -1;

    const draw = () => {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, width, height);
      
      ctx.font = '15px monospace';

      for (let i = 0; i < drops.length; i++) {
        ctx.fillStyle = defaultColor;
        const text = characters.charAt(Math.floor(Math.random() * characters.length));
        ctx.fillText(text, i * 20, drops[i] * 20);

        if (drops[i] * 20 > height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }

      // Logic for the special word drop
      if (wordY > height + specialWord.length * 20) {
          wordColumn = -1;
          wordY = -1;
      }
      
      // Small chance to start a new special word drop
      if (wordColumn === -1 && Math.random() > 0.995) {
          wordColumn = Math.floor(Math.random() * columns);
          wordY = 0;
      }

      if (wordColumn !== -1) {
          ctx.fillStyle = specialWordColor;
          for(let j = 0; j < specialWord.length; j++) {
              const yPos = wordY - (j * 20);
              if (yPos > 0 && yPos < height) {
                ctx.fillText(specialWord.charAt(j), wordColumn * 20, yPos);
              }
          }
          wordY += 20;
      }
    };

    const intervalId = setInterval(draw, 50);

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return <canvas ref={canvasRef} className="absolute top-0 left-0 w-full h-full z-0" />;
};

export default MatrixBackground;
