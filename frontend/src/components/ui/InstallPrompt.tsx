'use client';

import React from 'react';
import { Download, X, Smartphone } from 'lucide-react';
import { Button } from './Button';
import { Card, CardContent } from './Card';

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

export const InstallPrompt: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] = React.useState<BeforeInstallPromptEvent | null>(null);
  const [showPrompt, setShowPrompt] = React.useState(false);
  const [isInstalled, setIsInstalled] = React.useState(false);

  React.useEffect(() => {
    // Check if app is already installed
    const isRunningStandalone = window.matchMedia('(display-mode: standalone)').matches;
    const isNavigatorStandalone = (window.navigator as any).standalone === true;
    
    if (isRunningStandalone || isNavigatorStandalone) {
      setIsInstalled(true);
      return;
    }

    // Check if user has already dismissed the prompt
    const hasBeenDismissed = localStorage.getItem('pwa-install-dismissed');
    if (hasBeenDismissed) {
      return;
    }

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      
      // Show prompt after a delay to not be intrusive
      setTimeout(() => {
        setShowPrompt(true);
      }, 10000); // 10 seconds delay
    };

    const handleAppInstalled = () => {
      setIsInstalled(true);
      setShowPrompt(false);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;

    try {
      await deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      
      if (outcome === 'accepted') {
        console.log('User accepted the install prompt');
      } else {
        console.log('User dismissed the install prompt');
      }
    } catch (error) {
      console.error('Error during install:', error);
    }

    setDeferredPrompt(null);
    setShowPrompt(false);
  };

  const handleDismiss = () => {
    setShowPrompt(false);
    localStorage.setItem('pwa-install-dismissed', 'true');
  };

  if (isInstalled || !showPrompt || !deferredPrompt) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 sm:left-auto sm:max-w-sm">
      <Card className="bg-saffron-50 border-saffron-200">
        <CardContent className="p-4">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-saffron-100 rounded-full flex items-center justify-center">
                <Smartphone className="w-5 h-5 text-saffron-600" />
              </div>
            </div>
            
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-saffron-800">
                Install Palmistry AI
              </h3>
              
              <p className="text-xs mt-1 text-saffron-700">
                Add to your home screen for quick access to palm readings and faster performance.
              </p>

              <div className="mt-3 flex items-center space-x-2">
                <Button
                  size="sm"
                  onClick={handleInstallClick}
                  className="bg-saffron-600 hover:bg-saffron-700 text-white text-xs h-8"
                >
                  <Download className="w-3 h-3 mr-1" />
                  Install
                </Button>
                
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleDismiss}
                  className="text-saffron-600 border-saffron-300 hover:border-saffron-400 text-xs h-8"
                >
                  <X className="w-3 h-3 mr-1" />
                  Not Now
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};