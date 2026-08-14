"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function EnterTrackingPage() {
  const [code, setCode] = useState("");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.trim()) {
      router.push(`/track/${encodeURIComponent(code.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <div className="max-w-3xl mx-auto flex items-center">
          <span className="text-2xl mr-2">📦</span>
          <h1 className="text-xl font-bold">Mela Express</h1>
        </div>
      </header>

      <main className="flex-grow flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
          <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
            Track Your Parcel
          </h2>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label
                htmlFor="trackingCode"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Tracking Code
              </label>
              <input
                id="trackingCode"
                type="text"
                placeholder="e.g. MEX-HW-000482"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition"
            >
              Track Parcel
            </button>
          </form>
        </div>
      </main>

      <footer className="py-6 text-center text-sm text-gray-500">
        <p>Powered by Mela Express</p>
      </footer>
    </div>
  );
}
