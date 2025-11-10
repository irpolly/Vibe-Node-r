
import React from 'react';
import MatrixBackground from '../components/ui/MatrixBackground.tsx';

interface WelcomePageProps {
  onEnter: () => void;
}

const WelcomePage: React.FC<WelcomePageProps> = ({ onEnter }) => {
  return (
    <div className="relative w-screen h-screen bg-black flex flex-col items-center justify-center overflow-hidden">
      <MatrixBackground />
      <div className="relative z-10 text-center p-4 animate-fade-in">
        <h1 className="text-5xl md:text-7xl font-mono font-bold text-blue-400" style={{ textShadow: '0 0 10px #ff00ff, 0 0 20px #ff00ff' }}>
          Welcome to Vibe Node(r)
        </h1>
        <p className="text-green-300/80 mt-4 text-lg">Design your multi-agent reality.</p>
        <div className="mt-12">
          <button
            onClick={onEnter}
            className="px-8 py-4 bg-red-600 text-white font-bold text-lg rounded-full shadow-[0_0_15px_rgba(255,0,0,0.7)] hover:bg-red-700 hover:shadow-[0_0_25px_rgba(255,0,0,0.9)] transition-all duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-red-500/50"
          >
            Enter
          </button>
        </div>
      </div>
    </div>
  );
};

export default WelcomePage;
