'use client';
import React, { useState, useEffect } from 'react';
import Script from 'next/script';

interface BranchInfo {
  name: string;
  city: string;
  phone: string;
  address: string;
}

const BRANCHES: BranchInfo[] = [
  { name: 'Addis Ababa Central Hub', city: 'Addis Ababa', phone: '+251911000001', address: 'Bole Road, Mega Building, Ground Floor' },
  { name: 'Hawassa Regional Branch', city: 'Hawassa', phone: '+251911000002', address: 'Piazza Commercial Center' },
  { name: 'Adama Express Hub', city: 'Adama', phone: '+251911000003', address: 'Posta Bet Area, Main Highway' },
  { name: 'Dire Dawa Branch', city: 'Dire Dawa', phone: '+251911000004', address: 'Kazira Commercial District' },
  { name: 'Bahir Dar Hub', city: 'Bahir Dar', phone: '+251911000005', address: 'Near Lake Tana Port Road' },
  { name: 'Gondar Branch', city: 'Gondar', phone: '+251911000006', address: 'Arada Main Square' },
  { name: 'Mekelle Branch', city: 'Mekelle', phone: '+251911000007', address: 'Romanat Square, Kedamay Weyane' },
  { name: 'Jimma Branch', city: 'Jimma', phone: '+251911000008', address: 'Hermata Commercial Zone' },
];

export default function TelegramMiniApp() {
  const [activeTab, setActiveTab] = useState<'track' | 'calc' | 'branches' | 'pay'>('track');
  const [trackingInput, setTrackingInput] = useState('');
  const [trackingResult, setTrackingResult] = useState<any>(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [trackingError, setTrackingError] = useState('');

  // Price Calculator State
  const [calcOrigin, setCalcOrigin] = useState('Addis Ababa');
  const [calcDest, setCalcDest] = useState('Hawassa');
  const [calcWeight, setCalcWeight] = useState(2);

  // Telegram WebApp user
  const [tgUser, setTgUser] = useState<string>('Guest');

  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).Telegram?.WebApp) {
      const webapp = (window as any).Telegram.WebApp;
      webapp.ready();
      webapp.expand();
      if (webapp.initDataUnsafe?.user?.first_name) {
        setTgUser(webapp.initDataUnsafe.user.first_name);
      }
    }
  }, []);

  const handleTrack = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trackingInput.trim()) return;
    setTrackingLoading(true);
    setTrackingError('');
    setTrackingResult(null);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/parcels/track/${trackingInput.trim().toUpperCase()}`);
      if (!res.ok) {
        throw new Error('Parcel not found. Please check your tracking code.');
      }
      const data = await res.json();
      setTrackingResult(data);
    } catch (err: any) {
      setTrackingError(err.message || 'Unable to fetch parcel tracking details.');
    } finally {
      setTrackingLoading(false);
    }
  };

  // Calculate estimated price
  const calculatePrice = () => {
    const base = calcOrigin === calcDest ? 100 : 250;
    const perKg = 40;
    const weightFee = Math.max(0, calcWeight - 1) * perKg;
    return base + weightFee;
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-20">
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />

      {/* Top Telegram Header Bar */}
      <header className="bg-blue-600 text-white p-4 shadow-md sticky top-0 z-30">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center font-black text-white text-base">
              M
            </div>
            <div>
              <h1 className="font-extrabold text-sm tracking-tight leading-none">MELA EXPRESS</h1>
              <p className="text-[10px] text-blue-100 mt-0.5">Telegram Mini App</p>
            </div>
          </div>
          <div className="text-right">
            <span className="text-xs bg-blue-700/80 px-2.5 py-1 rounded-full text-blue-100 font-medium">
              👋 {tgUser}
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-md mx-auto p-4 space-y-4">
        {/* Tab Navigation */}
        <div className="grid grid-cols-4 gap-1.5 bg-white p-1.5 rounded-2xl shadow-sm border border-slate-200 text-xs font-bold">
          <button
            onClick={() => setActiveTab('track')}
            className={`py-2 rounded-xl transition ${activeTab === 'track' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            📍 Track
          </button>
          <button
            onClick={() => setActiveTab('calc')}
            className={`py-2 rounded-xl transition ${activeTab === 'calc' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            ⚖️ Price
          </button>
          <button
            onClick={() => setActiveTab('branches')}
            className={`py-2 rounded-xl transition ${activeTab === 'branches' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            🏢 Hubs
          </button>
          <button
            onClick={() => setActiveTab('pay')}
            className={`py-2 rounded-xl transition ${activeTab === 'pay' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'}`}
          >
            💳 Pay
          </button>
        </div>

        {/* TAB 1: TRACKING */}
        {activeTab === 'track' && (
          <div className="space-y-4">
            <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200">
              <h2 className="text-sm font-extrabold text-slate-900 mb-2">Track Any Shipment</h2>
              <form onSubmit={handleTrack} className="space-y-3">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="e.g. MEX-HW-752763"
                    value={trackingInput}
                    onChange={(e) => setTrackingInput(e.target.value)}
                    className="w-full pl-4 pr-10 py-3 bg-slate-50 border border-slate-300 rounded-2xl text-sm font-mono uppercase font-bold focus:bg-white focus:border-blue-600 outline-none transition"
                  />
                  {trackingInput && (
                    <button
                      type="button"
                      onClick={() => setTrackingInput('')}
                      className="absolute right-3 top-3 text-slate-400 font-bold text-sm"
                    >
                      ✕
                    </button>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={trackingLoading || !trackingInput.trim()}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 rounded-2xl text-sm shadow-md shadow-blue-500/20 disabled:opacity-50 transition"
                >
                  {trackingLoading ? 'Searching...' : '🔍 Track Package'}
                </button>
              </form>
            </div>

            {trackingError && (
              <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-4 rounded-2xl font-medium">
                {trackingError}
              </div>
            )}

            {trackingResult && (
              <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200 space-y-4">
                <div className="flex justify-between items-start border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-xs text-slate-400 font-bold uppercase">Tracking Code</span>
                    <h3 className="font-mono font-black text-lg text-blue-600">{trackingResult.tracking_code}</h3>
                  </div>
                  <span className="px-2.5 py-1 text-[11px] font-extrabold uppercase rounded-full bg-blue-100 text-blue-800">
                    {trackingResult.status?.replace(/_/g, ' ')}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs bg-slate-50 p-3 rounded-2xl border border-slate-100">
                  <div>
                    <span className="text-slate-400 font-bold uppercase block text-[10px]">Route</span>
                    <span className="font-bold text-slate-900">{trackingResult.origin_branch_name} ➔ {trackingResult.destination_branch_name}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 font-bold uppercase block text-[10px]">Payment</span>
                    <span className={`font-bold capitalize ${trackingResult.payment_status === 'paid' ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {trackingResult.payment_status}
                    </span>
                  </div>
                </div>

                {/* Timeline */}
                <div>
                  <h4 className="text-xs font-bold text-slate-800 uppercase mb-3">Live Progress</h4>
                  <div className="space-y-3 pl-2 border-l-2 border-blue-200">
                    {trackingResult.status_history?.map((step: any, idx: number) => (
                      <div key={idx} className="relative pl-4">
                        <div className="absolute -left-[17px] top-1 w-2.5 h-2.5 rounded-full bg-blue-600 border-2 border-white ring-2 ring-blue-100"></div>
                        <p className="text-xs font-bold text-slate-900 capitalize">{step.to_status?.replace(/_/g, ' ')}</p>
                        {step.note && <p className="text-[11px] text-slate-500">{step.note}</p>}
                        <span className="text-[10px] text-slate-400 font-mono">{new Date(step.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: PRICE CALCULATOR */}
        {activeTab === 'calc' && (
          <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200 space-y-4">
            <h2 className="text-sm font-extrabold text-slate-900">Delivery Fee Calculator</h2>
            
            <div className="space-y-3 text-xs font-bold">
              <div>
                <label className="block text-slate-600 mb-1">Origin City</label>
                <select
                  value={calcOrigin}
                  onChange={(e) => setCalcOrigin(e.target.value)}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-2xl outline-none"
                >
                  {BRANCHES.map(b => <option key={b.city} value={b.city}>{b.city}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-slate-600 mb-1">Destination City</label>
                <select
                  value={calcDest}
                  onChange={(e) => setCalcDest(e.target.value)}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-2xl outline-none"
                >
                  {BRANCHES.map(b => <option key={b.city} value={b.city}>{b.city}</option>)}
                </select>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-slate-600">Weight (Kilograms)</label>
                  <span className="text-blue-600 font-black text-sm">{calcWeight} KG</span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="50"
                  step="0.5"
                  value={calcWeight}
                  onChange={(e) => setCalcWeight(parseFloat(e.target.value))}
                  className="w-full accent-blue-600"
                />
              </div>
            </div>

            {/* Calculated Result Card */}
            <div className="bg-blue-50/70 border border-blue-200 p-4 rounded-2xl text-center">
              <span className="text-[11px] font-bold uppercase text-blue-700 block">Estimated Delivery Fee</span>
              <span className="text-2xl font-black text-blue-900 block my-1">{calculatePrice()} ETB</span>
              <span className="text-[11px] text-blue-600 font-medium">Estimated Delivery Time: 24–48 Hours</span>
            </div>
          </div>
        )}

        {/* TAB 3: BRANCH HUBS */}
        {activeTab === 'branches' && (
          <div className="space-y-3">
            <h2 className="text-sm font-extrabold text-slate-900 px-1">Regional Branch Hubs</h2>
            {BRANCHES.map((b) => (
              <div key={b.name} className="bg-white p-4 rounded-2xl shadow-sm border border-slate-200 space-y-1">
                <div className="flex justify-between items-start">
                  <h3 className="text-xs font-black text-slate-900">{b.name}</h3>
                  <span className="text-[10px] bg-slate-100 font-bold px-2 py-0.5 rounded-full text-slate-600">{b.city}</span>
                </div>
                <p className="text-[11px] text-slate-500">{b.address}</p>
                <div className="pt-2 flex items-center justify-between">
                  <a href={`tel:${b.phone}`} className="text-xs font-bold text-blue-600 flex items-center gap-1">
                    📞 {b.phone}
                  </a>
                  <span className="text-[10px] text-emerald-600 font-bold">Open 8:00 AM – 6:00 PM</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB 4: QUICK PAY */}
        {activeTab === 'pay' && (
          <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200 space-y-4">
            <h2 className="text-sm font-extrabold text-slate-900">Digital Payment Gateways</h2>
            <p className="text-xs text-slate-500">Pay for your shipment instantly using Ethiopian mobile wallets.</p>

            <div className="space-y-3 pt-2">
              <div className="p-4 border-2 border-emerald-500/30 bg-emerald-50/50 rounded-2xl flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-emerald-900 block">Telebirr Web & USSD Pay</span>
                  <span className="text-[11px] text-emerald-700">Fast 1-click mobile wallet checkout</span>
                </div>
                <span className="text-xl">📱</span>
              </div>

              <div className="p-4 border-2 border-blue-500/30 bg-blue-50/50 rounded-2xl flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-blue-900 block">CBE Birr & Chapa Gateway</span>
                  <span className="text-[11px] text-blue-700">Bank cards & commercial bank accounts</span>
                </div>
                <span className="text-xl">💳</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
