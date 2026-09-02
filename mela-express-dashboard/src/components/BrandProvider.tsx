'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  applyBrandToI18n,
  envBrand,
  getBrand,
  loadBrandFromApi,
  type BrandConfig,
} from '@/lib/brand';
import { displayName } from '@brand';

const BrandContext = createContext<BrandConfig>(getBrand());

export function BrandProvider({ children }: { children: ReactNode }) {
  const [brand, setBrand] = useState<BrandConfig>(getBrand());

  useEffect(() => {
    if (displayName(envBrand)) {
      applyBrandToI18n(envBrand);
      setBrand(envBrand);
      return;
    }
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) return;
    loadBrandFromApi(apiUrl)
      .then(setBrand)
      .catch(() => {
        /* env not set and API unreachable — i18n placeholders stay empty */
      });
  }, []);

  return <BrandContext.Provider value={brand}>{children}</BrandContext.Provider>;
}

export function useBrand(): BrandConfig {
  return useContext(BrandContext);
}
