export default function Loading() {
  return (
    <div className="min-h-screen bg-surface-100 flex items-center justify-center p-6">
      <div className="text-center">
        <div className="text-4xl mb-4 text-amber-500 animate-pulse">✦</div>
        <p className="text-gray-500 text-lg">Loading...</p>
      </div>
    </div>
  );
}
