'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from './Button';
import { Textarea } from './Textarea';

export type ModerationAction = 'submit' | 'approve' | 'reject' | 'request_changes';

interface ModerationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => void;
  action: ModerationAction;
  sessionTitle: string;
  confirmLabel: string;
  cancelLabel: string;
  title: string;
  message: string;
  reasonLabel?: string;
  reasonPlaceholder?: string;
  isLoading?: boolean;
}

export function ModerationDialog({
  isOpen,
  onClose,
  onConfirm,
  action,
  sessionTitle,
  confirmLabel,
  cancelLabel,
  title,
  message,
  reasonLabel,
  reasonPlaceholder,
  isLoading = false,
}: ModerationDialogProps) {
  const [reason, setReason] = useState('');

  // Reset reason when dialog opens
  useEffect(() => {
    if (isOpen) {
      setReason('');
    }
  }, [isOpen]);

  // Handle escape key
  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        onClose();
      }
    },
    [onClose, isLoading]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleEscape]);

  if (!isOpen) {
    return null;
  }

  const requiresReason = action === 'reject' || action === 'request_changes';
  const isValid = !requiresReason || reason.trim().length > 0;

  const getButtonVariant = () => {
    switch (action) {
      case 'reject':
        return 'danger';
      case 'approve':
      case 'submit':
        return 'primary';
      case 'request_changes':
        return 'secondary';
      default:
        return 'primary';
    }
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !isLoading) {
      onClose();
    }
  };

  const handleConfirm = () => {
    if (isValid) {
      onConfirm(requiresReason ? reason : undefined);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6"
        role="dialog"
        aria-modal="true"
        aria-labelledby="moderation-dialog-title"
      >
        <h2
          id="moderation-dialog-title"
          className="text-lg font-semibold text-slate-900 dark:text-white mb-2"
        >
          {title}
        </h2>

        <p className="text-slate-600 dark:text-slate-400 mb-2">
          <span className="font-medium">{sessionTitle}</span>
        </p>

        <p className="text-slate-600 dark:text-slate-400 mb-4">
          {message}
        </p>

        {requiresReason && (
          <div className="mb-6">
            <Textarea
              label={reasonLabel}
              placeholder={reasonPlaceholder}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={4}
              disabled={isLoading}
              autoFocus
            />
          </div>
        )}

        <div className="flex justify-end gap-3">
          <Button variant="ghost" onClick={onClose} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button
            variant={getButtonVariant()}
            onClick={handleConfirm}
            isLoading={isLoading}
            disabled={!isValid}
          >
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
