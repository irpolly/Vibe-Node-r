
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

    let columns = Math.floor(width / 20);
    const drops: { y: number; isWord: boolean; wordIndex: number; fallUntil: number | null }[] = [];
    for (let i = 0; i < columns; i++) {
      drops[i] = { y: 1, isWord: false, wordIndex: 0, fallUntil: null };
    }

    const characters = '的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下';
    const specialWord = ['V', 'i', 'b', 'e', 'N', 'o', 'd', 'e', '(r)'];
    const specialWordColor = '#FF0000'; // Red
    const defaultColor = '#800020'; // Burgundy

    const draw = () => {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, width, height);
      
      ctx.font = 'bold 15px monospace';
      ctx.textAlign = 'center';

      for (let i = 0; i < drops.length; i++) {
        const drop = drops[i];
        let text;

        if (drop.isWord) {
          ctx.fillStyle = specialWordColor;
          
          // Use modulo to loop through the special word continuously
          text = specialWord[drop.wordIndex % specialWord.length];
          drop.wordIndex++;

          // Only stop the special fall when it reaches its random end point
          if (drop.fallUntil && drop.y * 20 > drop.fallUntil) {
            drop.isWord = false;
            drop.fallUntil = null;
          }
        } else {
          ctx.fillStyle = defaultColor;
          text = characters.charAt(Math.floor(Math.random() * characters.length));
        }
        
        ctx.fillText(text, i * 20 + 10, drop.y * 20);

        if (drop.y * 20 > height && Math.random() > 0.975) {
          drops[i].y = 0;
          drops[i].fallUntil = null;
          if (Math.random() < 0.02) {
            drops[i].isWord = true;
            drops[i].wordIndex = 0;
            drops[i].fallUntil = Math.random() * (height * 0.7) + (height * 0.2);
          } else {
            drops[i].isWord = false;
          }
        }
        drops[i].y++;
      }
    };

    const intervalId = setInterval(draw, 50);

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      
      const newColumns = Math.floor(width / 20);
      if (newColumns > columns) {
        for (let i = columns; i < newColumns; i++) {
          drops[i] = { y: 1, isWord: false, wordIndex: 0, fallUntil: null };
        }
      } else {
        drops.length = newColumns;
      }
      columns = newColumns;
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
