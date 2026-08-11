"use client";

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div className="min-h-screen bg-surface-100 flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4 text-red-500">⬡</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Kuch gadbad ho gayi!</h1>
        <p className="text-gray-500 mb-6">Error aa gaya — dubara try karo.</p>
        <button onClick={reset} className="btn-gold px-6 py-3 text-sm">Dubara Try Karo</button>
      </div>
    </div>
  );
}
