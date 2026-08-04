'use client';
import { useState } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { Branch } from '@/types';
import { useToast } from '@/components/ui/Toast';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function Branches() {
  const toast = useToast();
  const { data: branches, error, mutate, isLoading } = useSWR<Branch[]>('/branches', fetcher);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingBranch, setEditingBranch] = useState<Branch | null>(null);

  const openModal = (branch: Branch | null = null) => {
    setEditingBranch(branch);
    setIsModalOpen(true);
  };

  return (
    <RoleGuard allowedRoles={['admin', 'manager']}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Branch Management</h1>
            <p className="text-sm text-gray-500 mt-1">Manage hub locations, city hubs, and contact details.</p>
          </div>
          <button 
            onClick={() => openModal()} 
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow-sm transition"
          >
            + New Branch
          </button>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Code</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Branch Name</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">City / Hub</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Phone & Email</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3.5 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {isLoading ? (
                <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-400 text-sm">Loading branches...</td></tr>
              ) : branches?.map(b => (
                <tr key={b.id} className="hover:bg-gray-50/50 transition">
                  <td className="px-6 py-4 text-sm font-mono font-bold text-blue-600">{b.code}</td>
                  <td className="px-6 py-4 text-sm font-semibold text-gray-900">{b.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{b.city}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    <div>{b.phone || '-'}</div>
                    <div className="text-xs text-gray-400">{b.email || ''}</div>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`px-2.5 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${b.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'}`}>
                      {b.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm font-medium">
                    <button 
                      onClick={() => openModal(b)} 
                      className="text-blue-600 hover:text-blue-800 font-semibold"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {isModalOpen && (
          <BranchModal 
            branch={editingBranch} 
            onClose={() => setIsModalOpen(false)} 
            onSave={(msg: string) => { 
              mutate(); 
              setIsModalOpen(false); 
              toast.success(msg, 'Branch Saved');
            }} 
          />
        )}
      </div>
    </RoleGuard>
  );
}

function BranchModal({ branch, onClose, onSave }: any) {
  const toast = useToast();
  const [formData, setFormData] = useState(branch || {
    name: '', code: '', city: '', address: '', phone: '', email: '', is_active: true
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (branch?.id) {
        await api.patch(`/branches/${branch.id}`, formData);
        onSave(`Branch ${formData.name} updated successfully!`);
      } else {
        await api.post('/branches', formData);
        onSave(`Branch ${formData.name} created successfully!`);
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to save branch');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white p-6 sm:p-8 rounded-2xl w-full max-w-md shadow-2xl border border-gray-100">
        <h2 className="text-xl font-bold text-gray-900 mb-5">{branch ? 'Edit Branch' : 'Create New Branch'}</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Branch Code</label>
              <input 
                required 
                type="text" 
                placeholder="e.g. AA5"
                value={formData.code} 
                onChange={e => setFormData({...formData, code: e.target.value.toUpperCase()})} 
                className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none" 
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">City</label>
              <input 
                required 
                type="text" 
                placeholder="e.g. Addis Ababa"
                value={formData.city} 
                onChange={e => setFormData({...formData, city: e.target.value})} 
                className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none" 
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Branch Name</label>
            <input 
              required 
              type="text" 
              placeholder="e.g. Addis Ababa - CMC Hub"
              value={formData.name} 
              onChange={e => setFormData({...formData, name: e.target.value})} 
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">Phone</label>
            <input 
              type="text" 
              placeholder="e.g. +251111223344"
              value={formData.phone || ''} 
              onChange={e => setFormData({...formData, phone: e.target.value})} 
              className="w-full border border-gray-300 rounded-xl px-3 py-2 text-sm bg-gray-50 focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none" 
            />
          </div>
          <div className="flex items-center gap-2 pt-2">
            <input 
              type="checkbox" 
              id="branch_active"
              checked={formData.is_active} 
              onChange={e => setFormData({...formData, is_active: e.target.checked})} 
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" 
            />
            <label htmlFor="branch_active" className="text-sm font-semibold text-gray-700">Active Branch</label>
          </div>
          <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
            <button 
              type="button" 
              onClick={onClose} 
              className="px-4 py-2 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-100 transition"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              disabled={saving}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold shadow-sm transition disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Branch'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}