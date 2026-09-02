'use client';

import { useTranslation, LanguageToggle } from '@/lib/i18n';
import React, { useState, useEffect, useCallback } from 'react';
import Script from 'next/script';
import {
  authWithTelegram,
  fetchMyParcels,
  fetchPublicTrack,
  fetchBranches,
  fetchQuote,
  initiatePayment,
  fetchPickupCode,
  confirmReceipt,
  getCustomerToken,
} from '@/lib/customer-api';

type Tab = 'orders' | 'track' | 'calc' | 'branches' | 'pay';

interface BranchInfo {
  name: string;
  code: string;
  city: string;
  phone?: string;
}

export default function TelegramMiniApp() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<Tab>('orders');
  const [authReady, setAuthReady] = useState(false);
  const [authError, setAuthError] = useState('');
  const [customerName, setCustomerName] = useState('Guest');

  const [trackingInput, setTrackingInput] = useState('');
  const [trackingResult, setTrackingResult] = useState<any>(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [trackingError, setTrackingError] = useState('');

  const [orders, setOrders] = useState<any[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);

  const [branches, setBranches] = useState<BranchInfo[]>([]);
  const [calcWeight, setCalcWeight] = useState(2);
  const [calcDims, setCalcDims] = useState({ l: '', w: '', h: '' });
  const [quote, setQuote] = useState<any>(null);

  const [payCode, setPayCode] = useState('');
  const [payMsg, setPayMsg] = useState('');
  const [payLoading, setPayLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  const loadOrders = useCallback(async () => {
    if (!getCustomerToken()) return;
    setOrdersLoading(true);
    try {
      const data = await fetchMyParcels();
      setOrders(data);
    } catch {
      setOrders([]);
    } finally {
      setOrdersLoading(false);
    }
  }, []);

  useEffect(() => {
    async function boot() {
      const webapp = (window as any).Telegram?.WebApp;
      if (webapp) {
        webapp.ready();
        webapp.expand();
        webapp.setHeaderColor?.('#2563eb');
        if (webapp.initDataUnsafe?.user?.first_name) {
          setCustomerName(webapp.initDataUnsafe.user.first_name);
        }
        if (webapp.initData) {
          try {
            const session = await authWithTelegram(webapp.initData);
            setCustomerName(session.name || customerName);
            setAuthReady(true);
            await loadOrders();
            return;
          } catch (e: any) {
            setAuthError(e.message || t('link_phone_bot'));
          }
        }
      }
      if (getCustomerToken()) {
        setAuthReady(true);
        await loadOrders();
      }
      setAuthReady(true);
    }
    boot();
  }, [loadOrders, t]);

  useEffect(() => {
    if (activeTab === 'branches' && branches.length === 0) {
      fetchBranches().then(setBranches).catch(() => setBranches([]));
    }
  }, [activeTab, branches.length]);

  const handleTrack = async (code?: string) => {
    const c = (code || trackingInput).trim().toUpperCase();
    if (!c) return;
    setTrackingLoading(true);
    setTrackingError('');
    setTrackingResult(null);
    setActionMsg('');
    try {
      const data = await fetchPublicTrack(c);
      setTrackingResult(data);
      setTrackingInput(c);
    } catch (err: any) {
      setTrackingError(err.message || t('error_generic'));
    } finally {
      setTrackingLoading(false);
    }
  };

  const handleQuote = async () => {
    try {
      const data = await fetchQuote({
        weight_kg: calcWeight,
        length_cm: calcDims.l ? parseFloat(calcDims.l) : undefined,
        width_cm: calcDims.w ? parseFloat(calcDims.w) : undefined,
        height_cm: calcDims.h ? parseFloat(calcDims.h) : undefined,
      });
      setQuote(data);
    } catch {
      setQuote(null);
    }
  };

  const handlePay = async () => {
    if (!payCode.trim()) return;
    setPayLoading(true);
    setPayMsg('');
    try {
      const data = await initiatePayment(payCode.trim().toUpperCase());
      if (data.dev_confirmed) {
        setPayMsg(t('pay_success_dev'));
      } else if (data.checkout_url) {
        const webapp = (window as any).Telegram?.WebApp;
        if (webapp?.openLink) webapp.openLink(data.checkout_url);
        else window.open(data.checkout_url, '_blank');
        setPayMsg(t('pay_tab_body'));
      }
    } catch (e: any) {
      setPayMsg(e.message || t('error_generic'));
    } finally {
      setPayLoading(false);
    }
  };

  const handlePickup = async (code: string) => {
    try {
      const data = await fetchPickupCode(code);
      setActionMsg(`${t('pickup_code')}: ${data.pickup_code} — ${data.branch_name}`);
    } catch (e: any) {
      setActionMsg(e.message);
    }
  };

  const handleReceipt = async (code: string) => {
    try {
      await confirmReceipt(code);
      setActionMsg(t('receipt_ok'));
      await handleTrack(code);
    } catch (e: any) {
      setActionMsg(e.message);
    }
  };

  const tabBtn = (tab: Tab, label: string) => (
    <button
      type="button"
      onClick={() => setActiveTab(tab)}
      className={`py-2 rounded-xl transition text-[11px] ${activeTab === tab ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-600'}`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans pb-24">
      <LanguageToggle />
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />

      <header className="bg-blue-600 text-white p-4 shadow-md sticky top-0 z-30">
        <div className="max-w-md mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center font-black">M</div>
            <div>
              <h1 className="font-extrabold text-sm tracking-tight leading-none">MELA EXPRESS</h1>
              <p className="text-[10px] text-blue-100 mt-0.5">Telegram Mini App</p>
            </div>
          </div>
          <span className="text-xs bg-blue-700/80 px-2.5 py-1 rounded-full text-blue-100">👋 {customerName}</span>
        </div>
      </header>

      <main className="max-w-md mx-auto p-4 space-y-4">
        {!authReady && (
          <p className="text-center text-sm text-slate-500 py-8">{t('auth_loading')}</p>
        )}

        {authError && !getCustomerToken() && (
          <div className="bg-amber-50 border border-amber-200 text-amber-900 text-xs p-4 rounded-2xl">{authError}</div>
        )}

        <div className="grid grid-cols-5 gap-1 bg-white p-1.5 rounded-2xl shadow-sm border border-slate-200 font-bold">
          {tabBtn('orders', `📦 ${t('tab_orders')}`)}
          {tabBtn('track', `📍 ${t('tab_track')}`)}
          {tabBtn('calc', `⚖️ ${t('tab_calc')}`)}
          {tabBtn('branches', `🏢 ${t('tab_branches')}`)}
          {tabBtn('pay', `💳 ${t('tab_pay')}`)}
        </div>

        {activeTab === 'orders' && (
          <div className="space-y-3">
            <h2 className="text-sm font-extrabold px-1">{t('my_orders')}</h2>
            {ordersLoading ? (
              <p className="text-sm text-slate-500">{t('loading')}</p>
            ) : orders.length === 0 ? (
              <p className="text-xs text-slate-500 bg-white p-4 rounded-2xl border">{t('no_orders')}</p>
            ) : (
              orders.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => { setActiveTab('track'); handleTrack(p.tracking_code); }}
                  className="w-full text-left bg-white p-4 rounded-2xl border border-slate-200 shadow-sm"
                >
                  <div className="flex justify-between items-start">
                    <span className="font-mono font-bold text-blue-600 text-sm">{p.tracking_code}</span>
                    <span className="text-[10px] font-bold uppercase bg-slate-100 px-2 py-0.5 rounded-full">
                      {p.status?.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    {p.origin_branch_code} → {p.destination_branch_code} · {p.payment_status}
                  </p>
                </button>
              ))
            )}
          </div>
        )}

        {activeTab === 'track' && (
          <div className="space-y-4">
            <div className="bg-white rounded-3xl p-5 shadow-sm border border-slate-200">
              <h2 className="text-sm font-extrabold mb-2">{t('track_any')}</h2>
              <form onSubmit={(e) => { e.preventDefault(); handleTrack(); }} className="space-y-3">
                <input
                  type="text"
                  placeholder={t('pay_tracking_placeholder')}
                  value={trackingInput}
                  onChange={(e) => setTrackingInput(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-50 border border-slate-300 rounded-2xl text-sm font-mono uppercase font-bold focus:border-blue-600 outline-none"
                />
                <button
                  type="submit"
                  disabled={trackingLoading}
                  className="w-full bg-blue-600 text-white font-bold py-3 rounded-2xl text-sm disabled:opacity-50"
                >
                  {trackingLoading ? t('searching') : `🔍 ${t('track_btn')}`}
                </button>
              </form>
            </div>

            {trackingError && <div className="bg-rose-50 text-rose-800 text-xs p-4 rounded-2xl">{trackingError}</div>}
            {actionMsg && <div className="bg-emerald-50 text-emerald-800 text-xs p-4 rounded-2xl">{actionMsg}</div>}

            {trackingResult && (
              <div className="bg-white rounded-3xl p-5 shadow-sm border space-y-4">
                <div className="flex justify-between items-start">
                  <h3 className="font-mono font-black text-lg text-blue-600">{trackingResult.tracking_code}</h3>
                  <span className="text-[11px] font-bold uppercase bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    {trackingResult.status?.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-3 rounded-2xl">
                  <div><span className="text-slate-400 block">{t('route')}</span>{trackingResult.origin_branch_name} → {trackingResult.destination_branch_name}</div>
                  <div><span className="text-slate-400 block">{t('payment')}</span>{trackingResult.payment_status}</div>
                </div>
                {trackingResult.eta && (
                  <p className="text-xs text-slate-600">ETA: {trackingResult.eta.remaining_minutes} min</p>
                )}
                {trackingResult.flight?.flight_number && (
                  <p className="text-xs">✈️ {trackingResult.flight.flight_number} ({trackingResult.flight.status})</p>
                )}
                <div className="flex flex-wrap gap-2">
                  {trackingResult.payment_status === 'pending' && (
                    <button type="button" onClick={() => { setPayCode(trackingResult.tracking_code); setActiveTab('pay'); }}
                      className="text-xs font-bold bg-amber-100 text-amber-900 px-3 py-2 rounded-xl">💳 {t('pay_now')}</button>
                  )}
                  {trackingResult.status === 'ready_for_pickup' && getCustomerToken() && (
                    <button type="button" onClick={() => handlePickup(trackingResult.tracking_code)}
                      className="text-xs font-bold bg-violet-100 text-violet-900 px-3 py-2 rounded-xl">🔑 {t('show_otp')}</button>
                  )}
                  {trackingResult.status === 'delivered' && getCustomerToken() && (
                    <button type="button" onClick={() => handleReceipt(trackingResult.tracking_code)}
                      className="text-xs font-bold bg-emerald-100 text-emerald-900 px-3 py-2 rounded-xl">✅ {t('confirm_receipt')}</button>
                  )}
                </div>
                <div>
                  <h4 className="text-xs font-bold uppercase mb-2">{t('live_progress')}</h4>
                  <div className="space-y-2 border-l-2 border-blue-200 pl-3">
                    {(trackingResult.journey_events || trackingResult.status_history || []).slice(0, 8).map((step: any, idx: number) => (
                      <div key={idx} className="text-xs">
                        <p className="font-bold capitalize">{(step.to_status || step.event_type || '').replace(/_/g, ' ')}</p>
                        <p className="text-slate-400">{new Date(step.created_at || step.timestamp).toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'calc' && (
          <div className="bg-white rounded-3xl p-5 shadow-sm border space-y-4">
            <h2 className="text-sm font-extrabold">{t('calc_title')}</h2>
            <div>
              <label className="text-xs font-bold text-slate-600">{t('weight_kg')}: {calcWeight}</label>
              <input type="range" min="0.5" max="50" step="0.5" value={calcWeight} onChange={(e) => setCalcWeight(parseFloat(e.target.value))} className="w-full accent-blue-600" />
            </div>
            <div className="grid grid-cols-3 gap-2">
              {(['l', 'w', 'h'] as const).map((k) => (
                <input key={k} type="number" placeholder={t(k === 'l' ? 'length_cm' : k === 'w' ? 'width_cm' : 'height_cm')}
                  value={calcDims[k]} onChange={(e) => setCalcDims({ ...calcDims, [k]: e.target.value })}
                  className="p-2 border rounded-xl text-xs" />
              ))}
            </div>
            <button type="button" onClick={handleQuote} className="w-full bg-blue-600 text-white font-bold py-3 rounded-2xl text-sm">{t('calculate_price')}</button>
            {quote && (
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-2xl text-center">
                <span className="text-[11px] font-bold text-blue-700 block">{t('estimated_cost')}</span>
                <span className="text-2xl font-black text-blue-900">{quote.suggested_price} ETB</span>
                <span className="text-[11px] text-blue-600 block mt-1">{t('estimated_days')}</span>
              </div>
            )}
          </div>
        )}

        {activeTab === 'branches' && (
          <div className="space-y-3">
            <h2 className="text-sm font-extrabold px-1">{t('our_branches')}</h2>
            {branches.map((b) => (
              <div key={b.code} className="bg-white p-4 rounded-2xl border shadow-sm">
                <div className="flex justify-between">
                  <h3 className="text-xs font-black">{b.name}</h3>
                  <span className="text-[10px] bg-slate-100 px-2 py-0.5 rounded-full">{b.city}</span>
                </div>
                {b.phone && <a href={`tel:${b.phone}`} className="text-xs font-bold text-blue-600 mt-2 block">📞 {b.phone}</a>}
                <span className="text-[10px] text-emerald-600 font-bold">{t('open_hours')}</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'pay' && (
          <div className="bg-white rounded-3xl p-5 shadow-sm border space-y-4">
            <h2 className="text-sm font-extrabold">{t('pay_tab_title')}</h2>
            <p className="text-xs text-slate-500">{t('pay_tab_body')}</p>
            <input type="text" value={payCode} onChange={(e) => setPayCode(e.target.value)}
              placeholder={t('pay_tracking_placeholder')}
              className="w-full px-4 py-3 border rounded-2xl font-mono uppercase text-sm" />
            <button type="button" disabled={payLoading} onClick={handlePay}
              className="w-full bg-emerald-600 text-white font-bold py-3 rounded-2xl text-sm disabled:opacity-50">
              {payLoading ? t('loading') : `💳 ${t('pay_now')}`}
            </button>
            {payMsg && <p className="text-xs text-slate-600">{payMsg}</p>}
          </div>
        )}
      </main>
    </div>
  );
}
