
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
    const drops: { y: number; isWord: boolean; wordIndex: number }[] = [];
    for (let i = 0; i < columns; i++) {
      drops[i] = { y: 1, isWord: false, wordIndex: 0 };
    }

    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    const specialWord = ['V', 'i', 'b', 'e', 'N', 'o', 'd', 'e', '(r)'];
    const specialWordColor = '#ADFF2F'; // A yellowish-green
    const defaultColor = '#0F0';

    const draw = () => {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, width, height);
      
      ctx.font = '15px monospace';

      for (let i = 0; i < drops.length; i++) {
        const drop = drops[i];
        let text;

        if (drop.isWord) {
          ctx.fillStyle = specialWordColor;
          text = specialWord[drop.wordIndex];
          drop.wordIndex++;
          if (drop.wordIndex >= specialWord.length) {
            drop.isWord = false; // End of the word
          }
        } else {
          ctx.fillStyle = defaultColor;
          text = characters.charAt(Math.floor(Math.random() * characters.length));
        }
        
        ctx.fillText(text, i * 20, drop.y * 20);

        // Resetting the drop
        if (drop.y * 20 > height && Math.random() > 0.975) {
          drops[i].y = 0;
          // Small chance to start a new special word drop
          if (Math.random() < 0.02) {
            drops[i].isWord = true;
            drops[i].wordIndex = 0;
          } else {
            drops[i].isWord = false;
          }
        }
        drops[i].y++;
      }
    };

    const intervalId = setInterval(draw, 40);

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
