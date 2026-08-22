'use client';
import React, { createContext, useContext, useState, useEffect } from 'react';

export type Language = 'en' | 'am';

const translations: Record<Language, Record<string, string>> = {
  en: {
    dashboard: 'Dashboard',
    parcels: 'Parcels',
    manifests: 'Manifests',
    cash: 'Cash Reconciliation',
    reports: 'Reports & Analytics',
    branches: 'Branches',
    staff: 'Staff Users',
    overrides: 'Overrides Log',
    new_parcel: '+ New Parcel',
    create_manifest: 'Create Manifest',
    search_placeholder: 'Search tracking code or phone...',
    all_statuses: 'All Statuses',
    tracking: 'Tracking',
    sender_receiver: 'Sender / Receiver',
    route: 'Route',
    status: 'Status',
    payment: 'Payment',
    date: 'Date',
    actions: 'Actions',
    logout: 'Logout',
    origin: 'Origin Branch',
    destination: 'Destination Branch',
    sender_name: 'Sender Name',
    sender_phone: 'Sender Phone',
    receiver_name: 'Receiver Name',
    receiver_phone: 'Receiver Phone',
    weight: 'Weight (kg)',
    price: 'Delivery Fee (ETB)',
    payment_mode: 'Payment Mode',
    payment_method: 'Payment Method',
    prepaid: 'Prepaid (Sender pays)',
    postpaid: 'Postpaid (Pay on Delivery)',
    register_parcel: 'Register Parcel',
    collect_cash: 'Collect Cash Payment',
    print_waybill: 'Print Waybill Sticker',
    handover_pod: 'Verify Pickup & Handover',
    verified_otp: 'Verified via OTP',
    enter_otp: 'Enter 6-digit Pickup OTP',
    sign_here: 'Receiver Signature',
    clear_sig: 'Clear Signature',
    confirm_delivery: 'Confirm Handover & Deliver',
  },
  am: {
    dashboard: 'ዳሽቦርድ',
    parcels: 'ፓርሰሎች / እቃዎች',
    manifests: 'ማኒፌስቶች',
    cash: 'የጥሬ ገንዘብ ሂሳብ',
    reports: 'ሪፖርቶችና ትንታኔ',
    branches: 'ቅርንጫፎች',
    staff: 'ሰራተኞች',
    overrides: 'የማለፊያ ምዝገባ',
    new_parcel: '+ አዲስ እቃ መመዝገቢያ',
    create_manifest: 'ማኒፌስት ፍጠር',
    search_placeholder: 'የመከታተያ ኮድ ወይም ስልክ ፈልግ...',
    all_statuses: 'ሁሉም ሁኔታዎች',
    tracking: 'የመከታተያ ቁጥር',
    sender_receiver: 'ላኪ / ተቀባይ',
    route: 'መስመር',
    status: 'ሁኔታ',
    payment: 'ክፍያ',
    date: 'ቀን',
    actions: 'ተግባራት',
    logout: 'ውጣ',
    origin: 'መነሻ ቅርንጫፍ',
    destination: 'መድረሻ ቅርንጫፍ',
    sender_name: 'የላኪ ስም',
    sender_phone: 'የላኪ ስልክ',
    receiver_name: 'የተቀባይ ስም',
    receiver_phone: 'የተቀባይ ስልክ',
    weight: 'ክብደት (ኪ.ግ)',
    price: 'የማጓጓዣ ዋጋ (ብር)',
    payment_mode: 'የክፍያ አይነት',
    payment_method: 'የክፍያ መንገድ',
    prepaid: 'ቅድመ ክፍያ (ላኪ የሚከፍለው)',
    postpaid: 'ድህረ ክፍያ (ተቀባይ የሚከፍለው)',
    register_parcel: 'እቃውን መዝግብ',
    collect_cash: 'ጥሬ ገንዘብ ተቀበል',
    print_waybill: 'የእቃ መለያ ስቲከር አትም',
    handover_pod: 'ምስክርነትና እቃ ማስረከብ',
    verified_otp: 'በኦቲፒ የተረጋገጠ',
    enter_otp: 'ባለ 6 አሃዝ የይለፍ ቃል አስገባ',
    sign_here: 'የተቀባይ ፊርማ',
    clear_sig: 'ፊርማውን አጥፋ',
    confirm_delivery: 'እቃውን አስረክብ',
  }
};

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  language: 'en',
  setLanguage: () => {},
  t: (key: string) => key,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('mela_lang') as Language;
      if (saved && (saved === 'en' || saved === 'am')) {
        setLanguageState(saved);
      }
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    if (typeof window !== 'undefined') {
      localStorage.setItem('mela_lang', lang);
    }
  };

  const t = (key: string): string => {
    return translations[language]?.[key] || translations['en']?.[key] || key;
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useTranslation = () => useContext(I18nContext);
