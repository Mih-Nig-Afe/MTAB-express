'use client';
import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Branch, ClassificationPreview } from '@/types';
import { useToast } from '@/components/ui/Toast';
import { useTranslation } from '@/lib/i18n';

export default function ParcelForm() {
  const router = useRouter();
  const toast = useToast();
  const { t } = useTranslation();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState<ClassificationPreview | null>(null);
  
  const [formData, setFormData] = useState({
    origin_branch_id: '',
    destination_branch_id: '',
    sender_name: '',
    sender_phone: '',
    receiver_name: '',
    receiver_phone: '',
    description: '',
    weight_kg: 1,
    length_cm: '',
    width_cm: '',
    height_cm: '',
    content_category: 'general',
    price: 150,
    payment_mode: 'before',
    payment_method: 'cash'
  });

  useEffect(() => {
    api.get('/branches').then(res => {
      setBranches(res.data);
      if (res.data.length > 0) {
        setFormData(prev => ({ 
          ...prev, 
          origin_branch_id: res.data[0].id, 
          destination_branch_id: res.data.length > 1 ? res.data[1].id : res.data[0].id 
        }));
      }
    }).catch(() => {
      toast.error(t('failed_load_branches'), t('network_error_title'));
    });
  }, [toast, t]);

  const refreshClassification = useCallback(async () => {
    try {
      const res = await api.post<ClassificationPreview>('/parcels/classify-preview', {
        weight_kg: Number(formData.weight_kg) || undefined,
        length_cm: formData.length_cm ? Number(formData.length_cm) : undefined,
        width_cm: formData.width_cm ? Number(formData.width_cm) : undefined,
        height_cm: formData.height_cm ? Number(formData.height_cm) : undefined,
        content_category: formData.content_category,
      });
      setPreview(res.data);
      setFormData(prev => ({ ...prev, price: res.data.suggested_price }));
    } catch {
      /* preview is best-effort */
    }
  }, [formData.weight_kg, formData.length_cm, formData.width_cm, formData.height_cm, formData.content_category]);

  useEffect(() => {
    const timer = setTimeout(refreshClassification, 350);
    return () => clearTimeout(timer);
  }, [refreshClassification]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: name === 'weight_kg' || name === 'price' ? Number(value) : value 
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    if (formData.origin_branch_id === formData.destination_branch_id) {
      const msg = t('origin_dest_must_differ');
      setError(msg);
      toast.warning(msg, t('validation_warning_title'));
      setLoading(false);
      return;
    }

    try {
      const payload = {
        ...formData,
        length_cm: formData.length_cm ? Number(formData.length_cm) : undefined,
        width_cm: formData.width_cm ? Number(formData.width_cm) : undefined,
        height_cm: formData.height_cm ? Number(formData.height_cm) : undefined,
      };
      const res = await api.post('/parcels', payload);
      toast.success(t('parcel_registered_msg').replace('{code}', res.data.tracking_code), t('parcel_created_title'));
      router.push(`/parcels/${res.data.id}?sticker=1`);
    } catch (err: any) {
      const detail = err.response?.data?.detail || t('failed_create_parcel');
      const errMsg = typeof detail === 'string' ? detail : JSON.stringify(detail);
      setError(errMsg);
      toast.error(errMsg, t('creation_failed_title'));
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white shadow-sm rounded-2xl border border-gray-200 p-6 sm:p-8 space-y-6">
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-sm flex items-start gap-3">
          <span className="text-lg flex-shrink-0">⚠️</span>
          <div className="flex-1 font-medium">{error}</div>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('origin')}</label>
          <select 
            name="origin_branch_id" 
            value={formData.origin_branch_id} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
          >
            {branches.map(b => <option key={b.id} value={b.id}>{b.name} ({b.code} - {b.city})</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('destination')}</label>
          <select 
            name="destination_branch_id" 
            value={formData.destination_branch_id} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
          >
            {branches.map(b => <option key={b.id} value={b.id}>{b.name} ({b.code} - {b.city})</option>)}
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('sender_name_optional')}</label>
          <input type="text" name="sender_name" value={formData.sender_name} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder={t('sender_name_placeholder')} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('sender_phone')}</label>
          <input type="text" name="sender_phone" required value={formData.sender_phone} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder="0911223344" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('receiver_name')}</label>
          <input type="text" name="receiver_name" required value={formData.receiver_name} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder={t('receiver_name_placeholder')} />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('receiver_phone')}</label>
          <input type="text" name="receiver_phone" required value={formData.receiver_phone} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder="0922334455" />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('package_contents')}</label>
          <textarea name="description" rows={2} value={formData.description} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder={t('contents_placeholder')} />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('content_category')}</label>
          <select name="content_category" value={formData.content_category} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition">
            <option value="general">{t('content_general')}</option>
            <option value="documents">{t('content_documents')}</option>
            <option value="electronics">{t('content_electronics')}</option>
            <option value="clothing">{t('content_clothing')}</option>
            <option value="food">{t('content_food')}</option>
            <option value="fragile">{t('content_fragile')}</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('weight')}</label>
          <input type="number" step="0.1" name="weight_kg" required value={formData.weight_kg} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('length_cm')}</label>
          <input type="number" step="0.1" name="length_cm" value={formData.length_cm} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder="40" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('width_cm')}</label>
          <input type="number" step="0.1" name="width_cm" value={formData.width_cm} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder="30" />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('height_cm')}</label>
          <input type="number" step="0.1" name="height_cm" value={formData.height_cm} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" placeholder="20" />
        </div>

        {preview && (
          <div className="md:col-span-2 p-4 bg-blue-50 border border-blue-100 rounded-xl text-sm grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div><span className="text-gray-500 block text-xs">{t('size_category')}</span><strong>{t(`size_${preview.size_category}`)}</strong></div>
            <div><span className="text-gray-500 block text-xs">{t('volumetric_weight')}</span><strong>{preview.volumetric_weight_kg} kg</strong></div>
            <div><span className="text-gray-500 block text-xs">{t('chargeable_weight')}</span><strong>{preview.chargeable_weight_kg} kg</strong></div>
            <div><span className="text-gray-500 block text-xs">{t('price')}</span><strong>{preview.suggested_price} ETB</strong></div>
            <p className="col-span-full text-xs text-blue-700">{t('auto_price_hint')}</p>
          </div>
        )}

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('price')}</label>
          <input type="number" name="price" required value={formData.price} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition" />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('payment_mode')}</label>
          <select name="payment_mode" value={formData.payment_mode} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition">
            <option value="before">{t('prepaid_intake')}</option>
            <option value="after">{t('postpaid_delivery')}</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">{t('payment_method')}</label>
          <select name="payment_method" value={formData.payment_method} onChange={handleChange} className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition">
            <option value="cash">{t('cash_counter')}</option>
            <option value="chapa">{t('chapa_gateway')}</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-6 border-t border-gray-100">
        <button type="button" onClick={() => router.back()} className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl text-sm transition">{t('cancel')}</button>
        <button type="submit" disabled={loading} className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm shadow-md disabled:opacity-60 transition">
          {loading ? t('creating') : t('register_parcel')}
        </button>
      </div>
    </form>
  );
}
