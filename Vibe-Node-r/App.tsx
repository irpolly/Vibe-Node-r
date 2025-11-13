
import React, { useState } from 'react';
import BuilderPage from './pages/BuilderPage.tsx';
import OutputPage from './pages/OutputPage.tsx';
import WelcomePage from './pages/WelcomePage.tsx';

export type AppState = 'welcome' | 'builder' | 'output';

const App: React.FC = () => {
  const [appState, setAppState] = useState<AppState>('welcome');
  const [workflowId, setWorkflowId] = useState<string | null>(null);

  const handleEnter = () => {
    setAppState('builder');
  };

  const handleFinalizeSuccess = (id: string) => {
    setWorkflowId(id);
    setAppState('output');
  };

  const handleBackToBuilder = () => {
    setWorkflowId(null);
    setAppState('builder');
  };

  switch (appState) {
    case 'welcome':
      return <WelcomePage onEnter={handleEnter} />;
    case 'builder':
      return <BuilderPage onFinalizeSuccess={handleFinalizeSuccess} />;
    case 'output':
      return <OutputPage onBack={handleBackToBuilder} workflowId={workflowId} />;
    default:
      return <WelcomePage onEnter={handleEnter} />;
  }
};

export default App;
