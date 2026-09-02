'use client';
import React, { useState, useRef } from 'react';
import { api } from '@/lib/api';
import { useToast } from '@/components/ui/Toast';
import { Parcel } from '@/types';
import { useTranslation } from '@/lib/i18n';

interface PoDModalProps {
  parcel: Parcel;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ProofOfDeliveryModal({ parcel, onClose, onSuccess }: PoDModalProps) {
  const { t } = useTranslation();
  const toast = useToast();
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatingOtp, setGeneratingOtp] = useState(false);
  const [hasSigned, setHasSigned] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isDrawing = useRef(false);

  // Canvas drawing handlers for signature
  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    isDrawing.current = true;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#1E293B';

    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    ctx.beginPath();
    ctx.moveTo(clientX - rect.left, clientY - rect.top);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    ctx.lineTo(clientX - rect.left, clientY - rect.top);
    ctx.stroke();
    setHasSigned(true);
  };

  const stopDrawing = () => {
    isDrawing.current = false;
  };

  const clearSignature = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasSigned(false);
  };

  const handleGenerateOtp = async () => {
    setGeneratingOtp(true);
    try {
      const res = await api.post(`/parcels/${parcel.id}/otp`);
      toast.info(t('otp_generated_msg', { otp: String(res.data.pickup_otp ?? ''), phone: String(res.data.receiver_phone ?? '') }), t('otp_dispatched'));
      setOtp(res.data.pickup_otp); // Autofill for convenience in dev/testing
    } catch (err: any) {
      toast.error(t('failed_otp'));
    } finally {
      setGeneratingOtp(false);
    }
  };

  const handleVerifyAndDeliver = async () => {
    if (!otp.trim()) {
      toast.warning(t('enter_otp_please'), t('missing_otp'));
      return;
    }

    setLoading(true);
    try {
      let signatureUrl = '';
      if (hasSigned && canvasRef.current) {
        signatureUrl = canvasRef.current.toDataURL('image/png');
      }

      await api.post(`/parcels/${parcel.id}/verify-pickup`, {
        otp: otp.trim(),
        signature_url: signatureUrl,
        photo_url: '',
        notes: t('pod_notes')
      });

      toast.success(t('parcel_delivered_msg', { code: parcel.tracking_code }), t('handover_complete'));
      onSuccess();
    } catch (err: any) {
      const detail = err.response?.data?.detail || t('failed_verify_otp');
      toast.error(typeof detail === 'string' ? detail : JSON.stringify(detail), t('verification_failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl border border-gray-100 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="font-extrabold text-gray-900 text-xl">🔐 {t('pod_title')}</h3>
            <p className="text-xs text-gray-500 mt-0.5">{t('tracking_colon')}: <span className="font-mono font-bold text-blue-600">{parcel.tracking_code}</span></p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 font-bold text-lg">✕</button>
        </div>

        <div className="space-y-6">
          {/* Receiver Info Banner */}
          <div className="bg-blue-50/70 border border-blue-200/60 p-4 rounded-2xl flex items-center justify-between">
            <div>
              <span className="text-xs text-blue-700 font-bold uppercase block">{t('authorized_receiver')}</span>
              <p className="font-bold text-gray-900 text-sm mt-0.5">{parcel.receiver_name}</p>
              <p className="font-mono text-xs text-gray-600">{parcel.receiver_phone}</p>
            </div>
            <button
              type="button"
              onClick={handleGenerateOtp}
              disabled={generatingOtp}
              className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-2 rounded-xl shadow-sm transition"
            >
              {generatingOtp ? t('sending') : `📲 ${t('send_otp')}`}
            </button>
          </div>

          {/* OTP Input */}
          <div>
            <label className="block text-xs font-bold text-gray-700 uppercase mb-2">
              {t('enter_six_otp')}
            </label>
            <input
              type="text"
              maxLength={6}
              placeholder="e.g. 849201"
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
              className="w-full text-center tracking-[0.5em] font-mono text-2xl font-black py-3 bg-gray-50 border-2 border-gray-300 rounded-2xl focus:bg-white focus:border-blue-600 outline-none transition text-gray-900"
            />
          </div>

          {/* Digital Signature Pad */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label className="block text-xs font-bold text-gray-700 uppercase">
                {t('signature_pad')}
              </label>
              {hasSigned && (
                <button
                  type="button"
                  onClick={clearSignature}
                  className="text-xs text-rose-600 hover:text-rose-800 font-semibold"
                >
                  {t('clear_pad')}
                </button>
              )}
            </div>
            <div className="border-2 border-dashed border-gray-300 rounded-2xl overflow-hidden bg-gray-50/50 hover:bg-white transition relative">
              <canvas
                ref={canvasRef}
                width={400}
                height={140}
                onMouseDown={startDrawing}
                onMouseMove={draw}
                onMouseUp={stopDrawing}
                onMouseLeave={stopDrawing}
                onTouchStart={startDrawing}
                onTouchMove={draw}
                onTouchEnd={stopDrawing}
                className="w-full h-[140px] cursor-crosshair touch-none"
              />
              {!hasSigned && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none text-gray-400 text-xs font-medium">
                  ✍️ {t('sign_here_hint')}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold rounded-2xl text-sm transition"
            >
              {t('cancel')}
            </button>
            <button
              type="button"
              onClick={handleVerifyAndDeliver}
              disabled={loading}
              className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-2xl text-sm shadow-md shadow-emerald-500/20 disabled:opacity-50 transition"
            >
              {loading ? t('verifying') : `✓ ${t('confirm_handover')}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
