'use client';

import { useState, useEffect, useCallback } from 'react';
import { useTranslations } from 'next-intl';
import { useSearchParams } from 'next/navigation';
import { adminApi, AdminUser, GlobalRole } from '@/lib/api';
import { Card, Input, Select, Badge, Button, ConfirmDialog } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';

const ROLES: GlobalRole[] = ['SUPER_ADMIN', 'ORGANIZER', 'PARTNER', 'USER'];

export default function AdminUsersPage() {
  const t = useTranslations('SuperAdmin.userManagement');
  const tRoles = useTranslations('SuperAdmin.globalRoles');
  const tCommon = useTranslations('Common');
  const searchParams = useSearchParams();
  const { showSuccess, showError } = useToast();

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>(searchParams.get('role') || '');
  const [statusFilter, setStatusFilter] = useState<string>('');

  // Dialogs
  const [roleChangeUser, setRoleChangeUser] = useState<AdminUser | null>(null);
  const [newRole, setNewRole] = useState<GlobalRole | null>(null);
  const [statusChangeUser, setStatusChangeUser] = useState<AdminUser | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const params: { role?: GlobalRole; is_active?: boolean } = {};
    if (roleFilter) params.role = roleFilter as GlobalRole;
    if (statusFilter === 'active') params.is_active = true;
    if (statusFilter === 'inactive') params.is_active = false;

    const response = await adminApi.listUsers(params);

    if (response.error) {
      setError(response.error.message);
    } else if (response.data) {
      setUsers(response.data);
    }

    setIsLoading(false);
  }, [roleFilter, statusFilter]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Filter users by search term (client-side)
  const filteredUsers = users.filter((user) => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      user.email.toLowerCase().includes(searchLower) ||
      (user.full_name?.toLowerCase().includes(searchLower) ?? false)
    );
  });

  const handleRoleChange = (user: AdminUser, role: GlobalRole) => {
    if (role === user.global_role) return;
    setRoleChangeUser(user);
    setNewRole(role);
  };

  const confirmRoleChange = async () => {
    if (!roleChangeUser || !newRole) return;

    setIsSubmitting(true);
    const response = await adminApi.updateUserRole(roleChangeUser.id, newRole);

    if (response.error) {
      showError(response.error.message);
    } else if (response.data) {
      setUsers((prev) =>
        prev.map((u) => (u.id === roleChangeUser.id ? response.data! : u))
      );
      showSuccess(t('roleUpdated'));
    }

    setIsSubmitting(false);
    setRoleChangeUser(null);
    setNewRole(null);
  };

  const handleStatusToggle = (user: AdminUser) => {
    setStatusChangeUser(user);
  };

  const confirmStatusChange = async () => {
    if (!statusChangeUser) return;

    setIsSubmitting(true);
    const newStatus = !statusChangeUser.is_active;
    const response = await adminApi.updateUserStatus(statusChangeUser.id, newStatus);

    if (response.error) {
      showError(response.error.message);
    } else if (response.data) {
      setUsers((prev) =>
        prev.map((u) => (u.id === statusChangeUser.id ? response.data! : u))
      );
      showSuccess(t('statusUpdated'));
    }

    setIsSubmitting(false);
    setStatusChangeUser(null);
  };

  const roleOptions = [
    { value: '', label: t('allRoles') },
    ...ROLES.map((role) => ({ value: role, label: tRoles(role) })),
  ];

  const statusOptions = [
    { value: '', label: t('allStatuses') },
    { value: 'active', label: t('activeUsers') },
    { value: 'inactive', label: t('inactiveUsers') },
  ];

  if (error) {
    return (
      <Card>
        <Card.Content>
          <p style={{ color: 'var(--color-text-danger)' }}>{error}</p>
        </Card.Content>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <h2
        className="text-xl font-semibold"
        style={{ color: 'var(--color-text-primary)' }}
      >
        {t('title')}
      </h2>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <Input
            placeholder={t('searchPlaceholder')}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            options={roleOptions}
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
          />
        </div>
        <div className="w-full sm:w-48">
          <Select
            options={statusOptions}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          />
        </div>
      </div>

      {/* Users table */}
      <Card>
        <Card.Content className="p-0">
          {isLoading ? (
            <div className="p-6 space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-12 rounded"
                  style={{ backgroundColor: 'var(--color-bg-secondary)' }}
                />
              ))}
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="p-6 text-center">
              <p style={{ color: 'var(--color-text-muted)' }}>{t('noUsers')}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr
                    className="border-b"
                    style={{ borderColor: 'var(--color-border)' }}
                  >
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('name')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('email')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('role')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('status')}
                    </th>
                    <th
                      className="text-left p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('lastLogin')}
                    </th>
                    <th
                      className="text-right p-4 font-medium"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      {t('actions')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr
                      key={user.id}
                      className="border-b last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      style={{ borderColor: 'var(--color-border)' }}
                    >
                      <td className="p-4">
                        <span style={{ color: 'var(--color-text-primary)' }}>
                          {user.full_name || '-'}
                        </span>
                      </td>
                      <td className="p-4">
                        <span style={{ color: 'var(--color-text-secondary)' }}>
                          {user.email}
                        </span>
                        {!user.email_verified && (
                          <span
                            className="ml-2 text-xs"
                            style={{ color: 'var(--color-text-warning)' }}
                          >
                            ({t('unverified')})
                          </span>
                        )}
                      </td>
                      <td className="p-4">
                        <Select
                          options={ROLES.map((role) => ({
                            value: role,
                            label: tRoles(role),
                          }))}
                          value={user.global_role}
                          onChange={(e) =>
                            handleRoleChange(user, e.target.value as GlobalRole)
                          }
                          className="w-40"
                        />
                      </td>
                      <td className="p-4">
                        <Badge variant={user.is_active ? 'success' : 'danger'}>
                          {user.is_active ? t('active') : t('inactive')}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <span style={{ color: 'var(--color-text-muted)' }}>
                          {user.last_login
                            ? new Date(user.last_login).toLocaleString()
                            : '-'}
                        </span>
                      </td>
                      <td className="p-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleStatusToggle(user)}
                        >
                          {user.is_active ? t('deactivate') : t('activate')}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card.Content>
      </Card>

      {/* Role change confirmation */}
      <ConfirmDialog
        isOpen={!!roleChangeUser && !!newRole}
        onClose={() => {
          setRoleChangeUser(null);
          setNewRole(null);
        }}
        onConfirm={confirmRoleChange}
        title={t('confirmRoleChangeTitle')}
        message={t('confirmRoleChangeMessage', {
          name: roleChangeUser?.full_name || roleChangeUser?.email || '',
          role: newRole ? tRoles(newRole) : '',
        })}
        confirmLabel={tCommon('save')}
        cancelLabel={tCommon('cancel')}
        isLoading={isSubmitting}
      />

      {/* Status change confirmation */}
      <ConfirmDialog
        isOpen={!!statusChangeUser}
        onClose={() => setStatusChangeUser(null)}
        onConfirm={confirmStatusChange}
        title={
          statusChangeUser?.is_active
            ? t('confirmDeactivateTitle')
            : t('confirmActivateTitle')
        }
        message={
          statusChangeUser?.is_active
            ? t('confirmDeactivateMessage', {
                name: statusChangeUser?.full_name || statusChangeUser?.email || '',
              })
            : t('confirmActivateMessage', {
                name: statusChangeUser?.full_name || statusChangeUser?.email || '',
              })
        }
        confirmLabel={
          statusChangeUser?.is_active ? t('deactivate') : t('activate')
        }
        cancelLabel={tCommon('cancel')}
        variant={statusChangeUser?.is_active ? 'danger' : 'default'}
        isLoading={isSubmitting}
      />
    </div>
  );
}
