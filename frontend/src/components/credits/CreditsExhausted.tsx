"use client";

export default function CreditsExhausted() {
  return (
    <div className="mx-4 mb-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-center">
      <p className="text-sm font-medium text-red-700">
        Hai esaurito i crediti giornalieri!
      </p>
      <p className="mt-1 text-xs text-red-600">
        I crediti gratuiti si resettano a mezzanotte.
      </p>
    </div>
  );
}
