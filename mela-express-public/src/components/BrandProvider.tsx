'use client';

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import {
  applyBrandToI18n,
  envBrand,
  loadBrandFromApi,
  type BrandConfig,
} from '@/lib/brand';
import { brandFromEnv, displayName } from '@brand';

function initialBrand(): BrandConfig {
  return displayName(envBrand) ? envBrand : brandFromEnv({});
}

const BrandContext = createContext<BrandConfig>(initialBrand());

export function BrandProvider({ children }: { children: ReactNode }) {
  const [brand, setBrand] = useState<BrandConfig>(initialBrand());

  useEffect(() => {
    const apply = (next: BrandConfig) => {
      applyBrandToI18n(next);
      setBrand(next);
    };

    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (apiUrl) {
      loadBrandFromApi(apiUrl)
        .then(apply)
        .catch(() => {
          if (displayName(envBrand)) apply(envBrand);
        });
      return;
    }
    if (displayName(envBrand)) apply(envBrand);
  }, []);

  return <BrandContext.Provider value={brand}>{children}</BrandContext.Provider>;
}

export function useBrand(): BrandConfig {
  return useContext(BrandContext);
}
