'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Branch } from '@/types';
import { useToast } from '@/components/ui/Toast';

export default function ParcelForm() {
  const router = useRouter();
  const toast = useToast();
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    origin_branch_id: '',
    destination_branch_id: '',
    sender_name: '',
    sender_phone: '',
    receiver_name: '',
    receiver_phone: '',
    description: '',
    weight_kg: 1,
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
      toast.error('Failed to load active branches from server', 'Network Error');
    });
  }, [toast]);

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
      const msg = 'Origin and destination branches must be different.';
      setError(msg);
      toast.warning(msg, 'Validation Warning');
      setLoading(false);
      return;
    }

    try {
      const res = await api.post('/parcels', formData);
      toast.success(`Parcel registered! Tracking Code: ${res.data.tracking_code}`, 'Parcel Created');
      router.push(`/parcels/${res.data.id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Failed to create parcel. Please try again.';
      const errMsg = typeof detail === 'string' ? detail : JSON.stringify(detail);
      setError(errMsg);
      toast.error(errMsg, 'Creation Failed');
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
          <label className="block text-sm font-semibold text-gray-700 mb-1">Origin Branch</label>
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
          <label className="block text-sm font-semibold text-gray-700 mb-1">Destination Branch</label>
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
          <label className="block text-sm font-semibold text-gray-700 mb-1">Sender Name (Optional)</label>
          <input 
            type="text" 
            name="sender_name" 
            value={formData.sender_name} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" 
            placeholder="e.g. Abebe Bikila" 
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Sender Phone</label>
          <input 
            type="text" 
            name="sender_phone" 
            required 
            value={formData.sender_phone} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" 
            placeholder="e.g. 0911223344" 
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Receiver Name</label>
          <input 
            type="text" 
            name="receiver_name" 
            required 
            value={formData.receiver_name} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" 
            placeholder="e.g. Tirunesh Dibaba" 
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Receiver Phone</label>
          <input 
            type="text" 
            name="receiver_phone" 
            required 
            value={formData.receiver_phone} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" 
            placeholder="e.g. 0922334455" 
          />
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-semibold text-gray-700 mb-1">Package Contents / Description</label>
          <textarea 
            name="description" 
            rows={2} 
            value={formData.description} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" 
            placeholder="e.g. Electronics, confidential documents, spare parts..." 
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Weight (kg)</label>
          <input 
            type="number" 
            step="0.1" 
            name="weight_kg" 
            required 
            value={formData.weight_kg} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" 
          />
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Delivery Fee (ETB)</label>
          <input 
            type="number" 
            name="price" 
            required 
            value={formData.price} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition" 
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Payment Mode</label>
          <select 
            name="payment_mode" 
            value={formData.payment_mode} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
          >
            <option value="before">Prepaid (Sender pays at intake)</option>
            <option value="after">Postpaid / Pay on Delivery (Receiver pays)</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">Payment Method</label>
          <select 
            name="payment_method" 
            value={formData.payment_method} 
            onChange={handleChange} 
            className="w-full bg-gray-50 border border-gray-300 rounded-xl py-2.5 px-3.5 text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
          >
            <option value="cash">Cash Counter</option>
            <option value="chapa">Chapa (Online Telebirr / CBE / Cards)</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-6 border-t border-gray-100">
        <button 
          type="button" 
          onClick={() => router.back()} 
          className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl text-sm transition"
        >
          Cancel
        </button>
        <button 
          type="submit" 
          disabled={loading} 
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold rounded-xl text-sm shadow-md shadow-blue-500/20 disabled:opacity-60 transition flex items-center gap-2"
        >
          {loading ? 'Creating...' : 'Register Parcel'}
        </button>
      </div>
    </form>
  );
}