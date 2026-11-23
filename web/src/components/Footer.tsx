import React from 'react';
import { Mail } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full border-t border-[var(--border-subtle)] bg-[var(--bg-header)] mt-auto py-6 px-4">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-[var(--text-muted)]">
        {/* Brand & Stack note */}
        <div className="flex items-center space-x-2">
          <span className="font-bold text-[var(--text-primary)]">POSEFIT.CV</span>
          <span>—</span>
          <span>On-device CV Kinematics</span>
        </div>

        {/* Creators Credits */}
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <span className="text-[var(--text-secondary)] font-semibold">Creators:</span>
          
          <div className="flex items-center space-x-1.5">
            <span className="text-[var(--text-primary)] font-medium">Aman Yadav</span>
            <a
              href="mailto:amanyadav2030a@gmail.com"
              className="text-[var(--text-muted)] hover:text-emerald-500 transition-colors inline-flex items-center"
              aria-label="Email Aman Yadav"
              title="amanyadav2030a@gmail.com"
            >
              <Mail className="w-3.5 h-3.5" />
            </a>
          </div>

          <div className="flex items-center space-x-1.5">
            <span className="text-[var(--text-primary)] font-medium">Hemang Bodana</span>
            <a
              href="mailto:hemangbodana123@gmail.com"
              className="text-[var(--text-muted)] hover:text-emerald-500 transition-colors inline-flex items-center"
              aria-label="Email Hemang Bodana"
              title="hemangbodana123@gmail.com"
            >
              <Mail className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Engine status indicator */}
        <div className="flex items-center space-x-1.5 text-[11px]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>Local Memory Only</span>
        </div>
      </div>
    </footer>
  );
};
