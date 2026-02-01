'use client';

interface PasswordStrengthProps {
  password: string;
}

export function PasswordStrength({ password }: PasswordStrengthProps) {
  const getStrength = (pwd: string): { score: number; label: string; color: string } => {
    if (!pwd) return { score: 0, label: '', color: 'bg-slate-600' };

    let score = 0;
    if (pwd.length >= 8) score++;
    if (pwd.length >= 12) score++;
    if (/[a-z]/.test(pwd) && /[A-Z]/.test(pwd)) score++;
    if (/\d/.test(pwd)) score++;
    if (/[^a-zA-Z0-9]/.test(pwd)) score++;

    if (score <= 2) return { score, label: 'Faible', color: 'bg-red-500' };
    if (score <= 3) return { score, label: 'Moyen', color: 'bg-amber-500' };
    return { score, label: 'Fort', color: 'bg-emerald-500' };
  };

  const strength = getStrength(password);

  if (!password) return null;

  return (
    <div className="flex items-center gap-2 mt-2">
      <div className="flex-1 h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all ${strength.color}`}
          style={{ width: `${(strength.score / 5) * 100}%` }}
        />
      </div>
      <span className="text-xs text-slate-500 dark:text-slate-400">{strength.label}</span>
    </div>
  );
}
