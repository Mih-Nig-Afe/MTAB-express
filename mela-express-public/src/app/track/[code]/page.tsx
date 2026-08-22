"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { use } from "react";

interface StatusEntry {
  to_status: string;
  timestamp: string;
  note?: string;
}

interface ParcelData {
  tracking_code: string;
  status: string;
  payment_status: string;
  origin_branch_name: string;
  destination_branch_name: string;
  status_history: StatusEntry[];
  created_at: string;
}

export default function TrackingPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const router = useRouter();
  const { code: rawCode } = use(params);
  const code = decodeURIComponent(rawCode);

  const [parcel, setParcel] = useState<ParcelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [searchCode, setSearchCode] = useState("");

  useEffect(() => {
    async function fetchTracking() {
      try {
        setLoading(true);
        const res = await fetch(`http://localhost:8000/api/parcels/track/${code}`);
        if (!res.ok) {
          if (res.status === 404) {
            setError(true);
          } else {
            throw new Error("Failed to fetch");
          }
        } else {
          const data = await res.json();
          setParcel(data);
          setError(false);
        }
      } catch (err) {
        console.error(err);
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    fetchTracking();
  }, [code]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchCode.trim()) {
      router.push(`/track/${encodeURIComponent(searchCode.trim())}`);
    }
  };

  const getStatusColor = (status: string) => {
    const s = status.toLowerCase();
    if (s.includes("delivered")) return "bg-green-600";
    if (s.includes("transit") || s.includes("assigned")) return "bg-blue-600";
    if (s.includes("pending")) return "bg-amber-500";
    if (s.includes("failed") || s.includes("cancelled")) return "bg-red-600";
    return "bg-gray-500";
  };

  const getStatusBg = (status: string) => {
    const s = status.toLowerCase();
    if (s.includes("delivered")) return "bg-green-100 text-green-800";
    if (s.includes("transit") || s.includes("assigned")) return "bg-blue-100 text-blue-800";
    if (s.includes("pending")) return "bg-amber-100 text-amber-800";
    if (s.includes("failed") || s.includes("cancelled")) return "bg-red-100 text-red-800";
    return "bg-gray-100 text-gray-800";
  };

  const formatDate = (isoStr: string) => {
    try {
      return new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "numeric",
      }).format(new Date(isoStr));
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div className="flex items-center cursor-pointer" onClick={() => router.push("/track/enter")}>
            <span className="text-2xl mr-2">📦</span>
            <h1 className="text-xl font-bold">Mela Express</h1>
          </div>
        </div>
      </header>

      <main className="flex-grow max-w-3xl w-full mx-auto p-4 py-8">
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : error || !parcel ? (
          <div className="bg-white rounded-xl shadow p-8 text-center">
            <div className="text-red-500 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Parcel Not Found</h2>
            <p className="text-gray-600 mb-6">We couldn't find a parcel with tracking code "{code}".</p>
            
            <form onSubmit={handleSearch} className="max-w-md mx-auto flex gap-2">
              <input
                type="text"
                placeholder="Try another tracking code"
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value)}
                className="flex-grow px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                required
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition"
              >
                Search
              </button>
            </form>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Header Card */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
                <div>
                  <p className="text-sm text-gray-500 font-medium uppercase tracking-wider mb-1">Tracking Code</p>
                  <h2 className="text-2xl md:text-3xl font-bold text-gray-900">{parcel.tracking_code}</h2>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      if (typeof window !== 'undefined') {
                        navigator.clipboard.writeText(window.location.href);
                        alert('Tracking link copied to clipboard!');
                      }
                    }}
                    className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-xs font-semibold transition flex items-center gap-1.5"
                  >
                    📋 Copy Link
                  </button>
                  <div className={`px-4 py-2 rounded-full font-semibold uppercase tracking-wide text-sm ${getStatusBg(parcel.status)}`}>
                    {parcel.status.replace(/_/g, ' ')}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-gray-100">
                <div>
                  <p className="text-sm text-gray-500 mb-1">Route</p>
                  <p className="font-medium text-gray-800 flex items-center gap-2">
                    {parcel.origin_branch_name}
                    <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                    {parcel.destination_branch_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-500 mb-1">Payment Status</p>
                  <p className="font-medium text-gray-800 capitalize">{parcel.payment_status.replace("_", " ")}</p>
                </div>
              </div>
            </div>

            {/* Timeline Card */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-6">Tracking History</h3>
              
              <div className="relative border-l-2 border-gray-200 ml-3 md:ml-4">
                {parcel.status_history.map((entry, index) => (
                  <div key={index} className="mb-8 pl-8 relative">
                    <div className={`absolute w-4 h-4 rounded-full -left-[9px] top-1 ${getStatusColor(entry.to_status)} ring-4 ring-white`}></div>
                    <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-1">
                      <div>
                        <p className="font-semibold text-gray-900 uppercase text-sm tracking-wide">{entry.to_status.replace(/_/g, " ")}</p>
                        {entry.note && (
                          <p className="text-gray-600 mt-1">{entry.note}</p>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 whitespace-nowrap">
                        {formatDate(entry.timestamp)}
                      </p>
                    </div>
                  </div>
                ))}
                {/* Created at entry if status_history doesn't implicitly start with it */}
                {parcel.status_history.length === 0 && (
                  <div className="mb-8 pl-8 relative">
                    <div className="absolute w-4 h-4 rounded-full -left-[9px] top-1 bg-gray-400 ring-4 ring-white"></div>
                    <div className="flex flex-col md:flex-row md:justify-between md:items-start gap-1">
                      <p className="font-semibold text-gray-900 uppercase text-sm tracking-wide">CREATED</p>
                      <p className="text-sm text-gray-500 whitespace-nowrap">
                        {formatDate(parcel.created_at)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="py-6 text-center text-sm text-gray-500">
        <p>Powered by Mela Express</p>
      </footer>
    </div>
  );
}
