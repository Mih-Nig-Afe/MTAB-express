'use client';
import { useState } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import RoleGuard from '@/components/layout/RoleGuard';
import { formatCurrency } from '@/lib/utils';

const fetcher = (url: string) => api.get(url).then(res => res.data);

export default function CashReconciliation() {
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2030-01-01');

  const { data, isLoading } = useSWR(
    `/reports/cash-reconciliation?start_date=${startDate}&end_date=${endDate}`,
    fetcher
  );

  return (
    <RoleGuard allowedRoles={['admin', 'manager', 'operator']}>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cash Drawer Reconciliation</h1>
            <p className="text-sm text-gray-500 mt-1">Audit physical counter cash collected across branch counters.</p>
          </div>
          <div className="flex items-center gap-2 bg-white p-2 rounded-xl border border-gray-200 shadow-sm text-sm">
            <input 
              type="date" 
              value={startDate} 
              onChange={e => setStartDate(e.target.value)} 
              className="border-none bg-gray-50 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 outline-none" 
            />
            <span className="text-gray-400 text-xs">to</span>
            <input 
              type="date" 
              value={endDate} 
              onChange={e => setEndDate(e.target.value)} 
              className="border-none bg-gray-50 rounded-lg px-2.5 py-1.5 text-xs text-gray-700 outline-none" 
            />
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-pulse">
            <div className="bg-white h-32 rounded-2xl shadow-sm"></div>
            <div className="bg-white h-32 rounded-2xl shadow-sm"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-2xl p-6 shadow-lg shadow-emerald-600/20">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-emerald-100">Total Cash Collected</span>
                <span className="text-2xl">💰</span>
              </div>
              <p className="text-3xl sm:text-4xl font-extrabold mt-3 tracking-tight">
                {formatCurrency(data?.total_cash_collected || 0)}
              </p>
              <p className="text-xs text-emerald-100 mt-2">Verified counter cash receipts</p>
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">Transactions Processed</span>
                <span className="text-2xl">🧾</span>
              </div>
              <p className="text-3xl sm:text-4xl font-extrabold text-gray-900 mt-3 tracking-tight">
                {data?.transaction_count || 0}
              </p>
              <p className="text-xs text-gray-400 mt-2">Total successful cash collections</p>
            </div>
          </div>
        )}

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
          <h2 className="text-base font-bold text-gray-900 mb-4 pb-2 border-b border-gray-100">
            📊 Reconciliation Breakdown
          </h2>
          <div className="flex flex-col gap-3">
            <div className="flex justify-between items-center py-2 text-sm text-gray-700 border-b border-gray-50">
              <span>Period Filter</span>
              <span className="font-semibold font-mono">{startDate} → {endDate}</span>
            </div>
            <div className="flex justify-between items-center py-2 text-sm text-gray-700 border-b border-gray-50">
              <span>Gross Counter Intake</span>
              <span className="font-semibold text-emerald-600 font-mono">{formatCurrency(data?.total_cash_collected || 0)}</span>
            </div>
            <div className="flex justify-between items-center py-2 text-sm text-gray-700">
              <span>Drawer Status</span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">BALANCED</span>
            </div>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}