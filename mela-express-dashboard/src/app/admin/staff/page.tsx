'use client';
import { useTranslation, labelFor } from '@/lib/i18n';
import { useState } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { Staff, Branch } from '@/types';
import { useToast } from '@/components/ui/Toast';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function StaffPage() {
  const { t } = useTranslation();
  const toast = useToast();
  const { data: staffList, error, mutate, isLoading } = useSWR<Staff[]>('/staff', fetcher);
  const { data: branches } = useSWR<Branch[]>('/branches', fetcher);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingStaff, setEditingStaff] = useState<Staff | null>(null);

  const openModal = (staff: Staff | null = null) => {
    setEditingStaff(staff);
    setIsModalOpen(true);
  };

  const getBranchName = (id?: string) => {
    if (!id) return t('all_hubs_admin');
    return branches?.find(b => b.id === id)?.name || id.substring(0, 8);
  };

  return (
    <RoleGuard allowedRoles={['admin', 'manager']}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{t('staff_management')}</h1>
            <p className="text-sm text-gray-500 mt-1">{t('staff_subtitle')}</p>
          </div>
          <button 
            onClick={() => openModal()} 
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow-sm transition"
          >
            + {t('new_staff')}
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto rounded-xl border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('name')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('role')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('branch')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('phone')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('status')}</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{t('actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {isLoading ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-400 text-sm">{t('loading_staff')}</td></tr>
              ) : staffList?.map(s => (
                <tr key={s.id} className="hover:bg-gray-50/50 transition">
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">{s.name}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className="px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800 capitalize">
                      {labelFor(t, 'role_', s.role)}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 font-medium">{getBranchName(s.branch_id)}</td>
                  <td className="px-6 py-4 text-sm font-mono text-gray-600">{s.phone}</td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${s.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                      {s.is_active ? t('active') : t('inactive')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium">
                    <button 
                      onClick={() => openModal(s)} 
                      className="text-blue-600 hover:text-blue-800 font-semibold"
                    >
                      {t('edit')}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>

        {isModalOpen && (
          <StaffModal 
            staff={editingStaff} 
            branches={branches || []}
            onClose={() => setIsModalOpen(false)} 
            onSave={(msg: string) => { 
              mutate(); 
              setIsModalOpen(false); 
              toast.success(msg, t('staff_updated_title'));
            }} 
          />
        )}
      </div>
    </RoleGuard>
  );
}

function StaffModal({ staff, branches, onClose, onSave }: any) {
  const { t } = useTranslation();
  const toast = useToast();
  const [formData, setFormData] = useState(staff || {
    name: '', phone: '', email: '', password: '', role: 'operator', branch_id: branches[0]?.id || '', is_active: true
  });
  const [showPassword, setShowPassword] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (staff?.id) {
        const payload = { ...formData };
        if (!payload.password) delete payload.password;
        await api.patch(`/staff/${staff.id}`, payload);
        onSave(`${t('staff_saved')}: ${formData.name}`);
      } else {
        if (!formData.password) {
          toast.warning(t('password_required_new'), t('missing_password'));
          setSaving(false);
          return;
        }
        await api.post('/staff', formData);
        onSave(`${t('staff_saved')}: ${formData.name}`);
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || t('failed_save_staff'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white p-6 sm:p-8 rounded-2xl w-full max-w-md shadow-2xl border border-gray-100 max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold text-gray-900 mb-5">{staff ? t('edit_staff') : t('add_staff')}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">{t('name')}</label>
            <input 
              required 
              type="text" 
              placeholder="e.g. Yonas Tadesse"
              value={formData.name} 
              onChange={e => setFormData({...formData, name: e.target.value})} 
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">{t('phone_number')}</label>
            <input 
              required 
              type="text" 
              placeholder="0911223344 or +251..."
              value={formData.phone} 
              onChange={e => setFormData({...formData, phone: e.target.value})} 
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
              {staff ? t('password_hint') : t('password')}
            </label>
            <div className="relative">
              <input 
                type={showPassword ? 'text' : 'password'}
                placeholder={staff ? '••••••••' : t('min_password')}
                value={formData.password || ''} 
                onChange={e => setFormData({...formData, password: e.target.value})} 
                className="w-full border border-gray-300 rounded-xl px-3 py-2 pr-10 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none" 
              />
              <button 
                type="button" 
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">{t('role')}</label>
              <select 
                value={formData.role} 
                onChange={e => setFormData({...formData, role: e.target.value})} 
                className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="operator">{t('role_operator')}</option>
                <option value="manager">{t('role_manager')}</option>
                <option value="driver">{t('role_driver')}</option>
                <option value="admin">{t('role_admin')}</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">{t('branch')}</label>
              <select 
                value={formData.branch_id || ''} 
                onChange={e => setFormData({...formData, branch_id: e.target.value})} 
                className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none"
              >
                <option value="">{t('none_hq_admin')}</option>
                {branches.map((b: any) => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <input 
              type="checkbox" 
              id="staff_active"
              checked={formData.is_active} 
              onChange={e => setFormData({...formData, is_active: e.target.checked})} 
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
            />
            <label htmlFor="staff_active" className="text-sm font-semibold text-gray-700">{t('active_account')}</label>
          </div>

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
            <button 
              type="button" 
              onClick={onClose} 
              className="px-4 py-2 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
            >
              {t('cancel')}
            </button>
            <button 
              type="submit" 
              disabled={saving}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-sm transition disabled:opacity-50"
            >
              {saving ? t('loading') : t('save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}