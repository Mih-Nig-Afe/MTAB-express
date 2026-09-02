'use client';
import React, { useEffect, useState } from 'react';
import { Parcel } from '@/types';
import { formatDate, formatCurrency } from '@/lib/utils';
import { api } from '@/lib/api';

interface WaybillProps {
  parcel: Parcel;
  originName: string;
  destName: string;
  onClose?: () => void;
}

export default function WaybillLabel({ parcel, originName, destName, onClose }: WaybillProps) {
  const [barcodeUrl, setBarcodeUrl] = useState('');
  const [qrUrl, setQrUrl] = useState('');

  useEffect(() => {
    let bc: string | null = null;
    let qr: string | null = null;
    (async () => {
      try {
        const [bcRes, qrRes] = await Promise.all([
          api.get(`/parcels/${parcel.id}/barcode.svg`, { responseType: 'blob' }),
          api.get(`/parcels/${parcel.id}/qr.svg`, { responseType: 'blob' }),
        ]);
        bc = URL.createObjectURL(bcRes.data);
        qr = URL.createObjectURL(qrRes.data);
        setBarcodeUrl(bc);
        setQrUrl(qr);
      } catch {
        /* sticker still printable with tracking text */
      }
    })();
    return () => {
      if (bc) URL.revokeObjectURL(bc);
      if (qr) URL.revokeObjectURL(qr);
    };
  }, [parcel.id]);

  const handlePrint = async () => {
    try {
      const res = await api.get(`/parcels/${parcel.id}/sticker`, { responseType: 'text' });
      const w = window.open('', '_blank', 'noopener');
      if (w) {
        w.document.write(res.data);
        w.document.close();
        w.focus();
        w.print();
      }
    } catch {
      if (typeof window !== 'undefined') window.print();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 print:p-0 print:bg-white print:static">
      <div className="bg-white rounded-2xl p-6 sm:p-8 max-w-lg w-full shadow-2xl border border-gray-100 print:shadow-none print:border-none print:p-0 print:max-w-none">
        <div className="flex justify-between items-center mb-4 print:hidden">
          <h3 className="font-bold text-gray-900 text-lg">Thermal Waybill Sticker (4×6&quot;)</h3>
          <div className="flex gap-2">
            <button onClick={handlePrint} className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-xl text-sm transition">
              Print Sticker
            </button>
            {onClose && (
              <button onClick={onClose} className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold px-3 py-2 rounded-xl text-sm transition">✕</button>
            )}
          </div>
        </div>

        <div className="border-4 border-black p-5 rounded-xl bg-white text-black font-sans print:border-4 print:w-[380px] mx-auto print:rounded-none">
          <div className="flex justify-between items-center border-b-2 border-black pb-3">
            <div>
              <h1 className="text-2xl font-black tracking-tighter">MELA EXPRESS</h1>
              <p className="text-[10px] font-bold tracking-wider uppercase text-gray-600">Scan at every checkpoint</p>
            </div>
            <div className="text-right">
              <span className="text-xs font-mono font-bold block">{formatDate(parcel.created_at)}</span>
              <span className={`text-[11px] font-extrabold uppercase px-2 py-0.5 border border-black rounded ${parcel.payment_status === 'paid' ? 'bg-black text-white' : 'bg-white text-black'}`}>
                {parcel.payment_status === 'paid' ? 'PAID' : 'COLLECT'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 border-b-2 border-black py-3 text-center">
            <div className="border-r-2 border-black pr-2">
              <span className="text-[10px] font-bold uppercase block text-gray-600">FROM</span>
              <span className="text-xl font-black uppercase tracking-tight block truncate">{originName}</span>
            </div>
            <div className="pl-2">
              <span className="text-[10px] font-bold uppercase block text-gray-600">TO</span>
              <span className="text-xl font-black uppercase tracking-tight block truncate">{destName}</span>
            </div>
          </div>

          <div className="py-4 border-b-2 border-black text-center flex flex-col items-center min-h-[80px]">
            {barcodeUrl ? (
              <img src={barcodeUrl} alt="Barcode" className="w-full max-h-16 object-contain" />
            ) : (
              <div className="h-14 w-full bg-gray-100 animate-pulse rounded" />
            )}
            <span className="text-xl font-black tracking-widest font-mono mt-1">{parcel.tracking_code}</span>
          </div>

          <div className="py-3 border-b-2 border-black flex justify-center min-h-[100px]">
            {qrUrl ? (
              <img src={qrUrl} alt="QR track link" className="w-24 h-24" />
            ) : (
              <div className="w-24 h-24 bg-gray-100 animate-pulse rounded" />
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 py-3 border-b-2 border-black text-xs">
            <div>
              <span className="font-bold uppercase text-[10px] block text-gray-600">SENDER</span>
              <p className="font-semibold">{parcel.sender_phone || '—'}</p>
            </div>
            <div>
              <span className="font-bold uppercase text-[10px] block text-gray-600">RECEIVER</span>
              <p className="font-black text-sm">{parcel.receiver_name}</p>
              <p className="font-mono font-bold text-xs">{parcel.receiver_phone}</p>
            </div>
          </div>

          <div className="flex justify-between items-center pt-3 text-xs">
            <div>
              <span className="text-[10px] font-bold uppercase text-gray-600 block">BILLABLE</span>
              <span className="font-black text-base">{parcel.chargeable_weight_kg || parcel.weight_kg || 1} KG</span>
            </div>
            <div>
              <span className="text-[10px] font-bold uppercase text-gray-600 block">FEE</span>
              <span className="font-black text-base">{formatCurrency(parcel.price)}</span>
            </div>
            <div className="text-right">
              <span className="text-[10px] font-bold uppercase text-gray-600 block">SIZE</span>
              <span className="font-bold uppercase">{parcel.size_category || '—'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
