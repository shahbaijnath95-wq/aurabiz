import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-surface-100 flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-4 text-amber-500">◈</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Page nahi mila!</h1>
        <p className="text-gray-500 mb-6">Yeh page exist nahi karta ya hata diya gaya.</p>
        <Link href="/" className="inline-block btn-gold px-6 py-3 text-sm">Home Pe Jao</Link>
      </div>
    </div>
  );
}
