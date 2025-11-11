import React from 'react';
import Button from '../ui/Button.tsx';
import Spinner from '../ui/Spinner.tsx';
import { TrashIcon, ResetIcon } from '../../constants.tsx';

interface ToolbarProps {
  onFinalize: () => void;
  onToggleDeleteMode: () => void;
  isDeletingMode: boolean;
  onShowSubmission: () => void;
  onResetLayout: () => void;
  isLoading: boolean;
}

const Toolbar: React.FC<ToolbarProps> = ({ onFinalize, onToggleDeleteMode, isDeletingMode, onShowSubmission, onResetLayout, isLoading }) => {
  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 bg-gray-800/80 backdrop-blur-sm border border-gray-700/50 rounded-full shadow-lg p-2 flex items-center gap-2">
      <h1 className="text-lg font-bold text-cyan-400 px-4">Vibe Node(r)</h1>
      <div className="w-px h-6 bg-gray-600"></div>
      <Button onClick={onResetLayout} variant="ghost">
        <ResetIcon className="w-5 h-5" />
        Reset
      </Button>
      <Button onClick={onToggleDeleteMode} variant="ghost" className={isDeletingMode ? 'text-red-400 bg-red-500/10' : ''}>
        <TrashIcon className="w-5 h-5" />
        Delete
      </Button>
      <Button onClick={onShowSubmission} variant="ghost">
        Hackathon
      </Button>
      <div className="w-px h-6 bg-gray-600"></div>
      <Button onClick={onFinalize} disabled={isLoading} variant="primary">
        {isLoading ? <><Spinner /> Finalizing...</> : 'Finalize & Run'}
      </Button>
    </div>
  );
};

export default Toolbar;
