import React, { forwardRef } from 'react';

interface EmulatorProps {
  src?: string | null;
  srcDoc?: string;
  title?: string;
}

/**
 * A component that renders a visual frame of a modern smartphone around its children,
 * typically an iframe, to create a realistic mobile preview.
 * It uses `forwardRef` to allow parent components to get a ref to the underlying iframe.
 * The `pointer-events-none` on the frame and `pointer-events-auto` on the screen ensure
 * that all user interactions are passed through to the iframe content.
 */
const Emulator = forwardRef<HTMLIFrameElement, EmulatorProps>(({ src, srcDoc, title = "Emulator Preview" }, ref) => {
  return (
    <div className="relative mx-auto border-gray-800 bg-gray-800 border-[14px] rounded-[2.5rem] h-[600px] w-[300px] shadow-xl pointer-events-none">
      {/* Notch */}
      <div className="w-[140px] h-[28px] bg-gray-800 top-0 rounded-b-[1rem] left-1/2 -translate-x-1/2 absolute z-20"></div>
      
      {/* Visual-only side buttons */}
      <div className="h-[46px] w-[3px] bg-gray-800 absolute -left-[17px] top-[72px] rounded-l-lg"></div>
      <div className="h-[46px] w-[3px] bg-gray-800 absolute -left-[17px] top-[124px] rounded-l-lg"></div>
      <div className="h-[64px] w-[3px] bg-gray-800 absolute -right-[17px] top-[142px] rounded-r-lg"></div>
      
      {/* Screen content - enables pointer events for the iframe */}
      <div className="rounded-[2rem] overflow-hidden w-full h-full bg-white pointer-events-auto">
        <iframe
          ref={ref}
          title={title}
          className="w-full h-full"
          sandbox="allow-scripts allow-same-origin"
          src={src || undefined}
          srcDoc={!src ? srcDoc : undefined}
        />
      </div>
    </div>
  );
});

Emulator.displayName = 'Emulator';

export default Emulator;
