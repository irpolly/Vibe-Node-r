import React, { forwardRef } from 'react';
import { twMerge } from 'tailwind-merge';

interface EmulatorProps {
  src?: string | null;
  srcDoc?: string;
  title?: string;
  orientation?: 'portrait' | 'landscape';
  isMobileView?: boolean;
}

/**
 * A component that renders a visual frame of a modern smartphone around its children.
 * It supports portrait and landscape orientations and can snap to a fullscreen view on mobile.
 */
const Emulator = forwardRef<HTMLIFrameElement, EmulatorProps>(({ 
  src, 
  srcDoc, 
  title = "Emulator Preview", 
  orientation = 'portrait',
  isMobileView = false
}, ref) => {

  const isLandscape = orientation === 'landscape';

  // Base dimensions
  const portraitClasses = 'h-[600px] w-[300px]';
  const landscapeClasses = 'h-[300px] w-[600px]';

  // Fullscreen classes for mobile view
  const mobileClasses = 'w-full h-full !rounded-none !border-0';

  const containerClasses = twMerge(
    'relative mx-auto border-gray-800 bg-gray-800 border-[14px] rounded-[2.5rem] shadow-xl transition-all duration-300 ease-in-out',
    isLandscape ? landscapeClasses : portraitClasses,
    isMobileView && mobileClasses,
    'pointer-events-none' // Make the frame non-interactive
  );

  const screenClasses = twMerge(
    'rounded-[2rem] overflow-hidden w-full h-full bg-white',
    isMobileView && '!rounded-none',
    'pointer-events-auto' // Allow interaction with the screen/iframe
  );

  return (
    <div className={containerClasses}>
      {/* Decorative elements, hidden in mobile view */}
      {!isMobileView && (
        <>
          {/* Notch */}
          <div className={twMerge(
            "bg-gray-800 absolute z-20",
            isLandscape 
              ? "w-[28px] h-[140px] top-1/2 -translate-y-1/2 -left-[28px] rounded-r-[1rem]" 
              : "w-[140px] h-[28px] top-0 left-1/2 -translate-x-1/2 rounded-b-[1rem]"
          )}></div>
          
          {/* Side buttons */}
          <div className={twMerge("bg-gray-800 absolute", isLandscape ? "h-[3px] w-[46px] -top-[17px] left-[72px] rounded-t-lg" : "h-[46px] w-[3px] -left-[17px] top-[72px] rounded-l-lg")}></div>
          <div className={twMerge("bg-gray-800 absolute", isLandscape ? "h-[3px] w-[46px] -top-[17px] left-[124px] rounded-t-lg" : "h-[46px] w-[3px] -left-[17px] top-[124px] rounded-l-lg")}></div>
          <div className={twMerge("bg-gray-800 absolute", isLandscape ? "h-[3px] w-[64px] -bottom-[17px] left-[142px] rounded-b-lg" : "h-[64px] w-[3px] -right-[17px] top-[142px] rounded-r-lg")}></div>
        </>
      )}
      
      {/* Screen content */}
      <div className={screenClasses}>
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
