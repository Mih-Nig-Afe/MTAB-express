'use client';
import React from 'react';
import { Parcel } from '@/types';
import { formatDate, formatCurrency } from '@/lib/utils';

interface WaybillProps {
  parcel: Parcel;
  originName: string;
  destName: string;
  onClose?: () => void;
}

export default function WaybillLabel({ parcel, originName, destName, onClose }: WaybillProps) {
  const handlePrint = () => {
    if (typeof window !== 'undefined') {
      window.print();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 print:p-0 print:bg-white print:static">
      <div className="bg-white rounded-2xl p-6 sm:p-8 max-w-lg w-full shadow-2xl border border-gray-100 print:shadow-none print:border-none print:p-0 print:max-w-none">
        <div className="flex justify-between items-center mb-4 print:hidden">
          <h3 className="font-bold text-gray-900 text-lg">🖨️ Thermal Waybill Sticker (4x6&quot;)</h3>
          <div className="flex gap-2">
            <button
              onClick={handlePrint}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-xl text-sm transition flex items-center gap-1.5 shadow-sm"
            >
              Print Sticker
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold px-3 py-2 rounded-xl text-sm transition"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* The 4x6" Thermal Sticker Box */}
        <div className="border-4 border-black p-5 rounded-xl bg-white text-black font-sans print:border-4 print:w-[380px] mx-auto print:rounded-none">
          {/* Header */}
          <div className="flex justify-between items-center border-b-2 border-black pb-3">
            <div>
              <h1 className="text-2xl font-black tracking-tighter">MELA EXPRESS</h1>
              <p className="text-[10px] font-bold tracking-wider uppercase text-gray-600">Inter-City Parcel Logistics</p>
            </div>
            <div className="text-right">
              <span className="text-xs font-mono font-bold block">{formatDate(parcel.created_at)}</span>
              <span className={`text-[11px] font-extrabold uppercase px-2 py-0.5 border border-black rounded ${parcel.payment_status === 'paid' ? 'bg-black text-white' : 'bg-white text-black'}`}>
                {parcel.payment_status === 'paid' ? 'PAID / የተከፈለ' : 'PAY ON DELIVERY'}
              </span>
            </div>
          </div>

          {/* Route Section */}
          <div className="grid grid-cols-2 gap-2 border-b-2 border-black py-3 text-center">
            <div className="border-r-2 border-black pr-2">
              <span className="text-[10px] font-bold uppercase block text-gray-600">FROM / መነሻ</span>
              <span className="text-xl font-black uppercase tracking-tight block truncate">{originName}</span>
            </div>
            <div className="pl-2">
              <span className="text-[10px] font-bold uppercase block text-gray-600">TO / መድረሻ</span>
              <span className="text-xl font-black uppercase tracking-tight block text-black truncate">{destName}</span>
            </div>
          </div>

          {/* Barcode & Tracking Block */}
          <div className="py-4 border-b-2 border-black text-center flex flex-col items-center">
            {/* SVG 1D Barcode Simulation */}
            <svg className="w-full h-14" viewBox="0 0 260 50">
              <rect x="10" y="0" width="4" height="40" fill="black" />
              <rect x="18" y="0" width="2" height="40" fill="black" />
              <rect x="24" y="0" width="6" height="40" fill="black" />
              <rect x="34" y="0" width="3" height="40" fill="black" />
              <rect x="42" y="0" width="5" height="40" fill="black" />
              <rect x="52" y="0" width="2" height="40" fill="black" />
              <rect x="60" y="0" width="7" height="40" fill="black" />
              <rect x="72" y="0" width="3" height="40" fill="black" />
              <rect x="80" y="0" width="5" height="40" fill="black" />
              <rect x="90" y="0" width="2" height="40" fill="black" />
              <rect x="98" y="0" width="6" height="40" fill="black" />
              <rect x="108" y="0" width="4" height="40" fill="black" />
              <rect x="116" y="0" width="3" height="40" fill="black" />
              <rect x="124" y="0" width="6" height="40" fill="black" />
              <rect x="136" y="0" width="2" height="40" fill="black" />
              <rect x="142" y="0" width="5" height="40" fill="black" />
              <rect x="152" y="0" width="3" height="40" fill="black" />
              <rect x="160" y="0" width="6" height="40" fill="black" />
              <rect x="170" y="0" width="4" height="40" fill="black" />
              <rect x="180" y="0" width="2" height="40" fill="black" />
              <rect x="188" y="0" width="5" height="40" fill="black" />
              <rect x="198" y="0" width="3" height="40" fill="black" />
              <rect x="206" y="0" width="7" height="40" fill="black" />
              <rect x="218" y="0" width="2" height="40" fill="black" />
              <rect x="226" y="0" width="5" height="40" fill="black" />
              <rect x="236" y="0" width="4" height="40" fill="black" />
              <rect x="246" y="0" width="3" height="40" fill="black" />
            </svg>
            <span className="text-xl font-black tracking-widest font-mono mt-1">{parcel.tracking_code}</span>
          </div>

          {/* Parties Info */}
          <div className="grid grid-cols-2 gap-3 py-3 border-b-2 border-black text-xs">
            <div>
              <span className="font-bold uppercase text-[10px] block text-gray-600">SENDER / ላኪ</span>
              <p className="font-semibold">{parcel.sender_phone}</p>
            </div>
            <div>
              <span className="font-bold uppercase text-[10px] block text-gray-600">RECEIVER / ተቀባይ</span>
              <p className="font-black text-sm">{parcel.receiver_name}</p>
              <p className="font-mono font-bold text-xs">{parcel.receiver_phone}</p>
            </div>
          </div>

          {/* Footer Metrics */}
          <div className="flex justify-between items-center pt-3 text-xs">
            <div>
              <span className="text-[10px] font-bold uppercase text-gray-600 block">WEIGHT</span>
              <span className="font-black text-base">{parcel.weight_kg || 1} KG</span>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase text-gray-600 block">FEE / ዋጋ</span>
              <span className="font-black text-base">{formatCurrency(parcel.price)}</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold uppercase text-gray-600 block">SUPPORT</span>
              <span className="font-mono font-bold text-[11px]">+251900000000</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
