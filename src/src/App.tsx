
import React, { useState } from 'react';
import BuilderPage from './pages/BuilderPage.tsx';
import OutputPage from './pages/OutputPage.tsx';

export type AppState = 'builder' | 'output';

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>('builder');
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  const handleFinalizeSuccess = (id: string) => {
    setWorkflowId(id);
    setAppState('output');
  };

  const handleBackToBuilder = () => {
    setWorkflowId(null);
    setAppState('builder');
  };

  if (appState === 'output') {
    return <OutputPage onBack={handleBackToBuilder} workflowId={workflowId} />;
  }

  return <BuilderPage onFinalizeSuccess={handleFinalizeSuccess} />;
};

export default App;
