'use client';
import { useEffect, useRef } from 'react';

export function useBarcodeScanner(onScan: (scannedCode: string) => void) {
  const buffer = useRef('');
  const lastKeyTime = useRef(0);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement;
      // Ignore if user is currently typing in an input or textarea
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable)) {
        return;
      }

      const now = Date.now();
      // Most hardware barcode guns type all characters in < 50ms intervals
      if (now - lastKeyTime.current > 100) {
        buffer.current = '';
      }
      lastKeyTime.current = now;

      if (e.key === 'Enter') {
        if (buffer.current.length >= 6) {
          onScan(buffer.current.trim());
          buffer.current = '';
        }
      } else if (e.key.length === 1) {
        buffer.current += e.key;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onScan]);
}
