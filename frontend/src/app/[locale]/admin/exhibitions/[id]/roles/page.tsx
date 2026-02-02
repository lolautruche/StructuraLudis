'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import {
  exhibitionsApi,
  zonesApi,
  Exhibition,
  ExhibitionRoleAssignment,
  ExhibitionRole,
  Zone,
  UserSearchResult,
} from '@/lib/api';
import { Card, Button, Select, Input, ConfirmDialog, Badge } from '@/components/ui';
import { useToast } from '@/contexts/ToastContext';

export default function ExhibitionRolesPage() {
  const params = useParams();
  const exhibitionId = params.id as string;
  const t = useTranslations('SuperAdmin.exhibitionRoles');
  const tCommon = useTranslations('Common');
  const tRoles = useTranslations('Common.exhibitionRoles');
  const { showSuccess, showError } = useToast();

  // Data states
  const [exhibition, setExhibition] = useState<Exhibition | null>(null);
  const [roles, setRoles] = useState<ExhibitionRoleAssignment[]>([]);
  const [zones, setZones] = useState<Zone[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedRole, setSelectedRole] = useState<ExhibitionRole>('ORGANIZER');
  const [selectedZoneIds, setSelectedZoneIds] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // User search states
  const [userSearch, setUserSearch] = useState('');
  const [searchResults, setSearchResults] = useState<UserSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UserSearchResult | null>(null);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const searchTimeout = useRef<NodeJS.Timeout | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // Edit states
  const [editingRole, setEditingRole] = useState<ExhibitionRoleAssignment | null>(null);
  const [editZoneIds, setEditZoneIds] = useState<string[]>([]);

  // Delete states
  const [deleteRole, setDeleteRole] = useState<ExhibitionRoleAssignment | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [exhibitionRes, rolesRes, zonesRes] = await Promise.all([
        exhibitionsApi.getById(exhibitionId),
        exhibitionsApi.listRoles(exhibitionId),
        zonesApi.list(exhibitionId),
      ]);

      if (exhibitionRes.error) {
        setError(exhibitionRes.error.message);
        return;
      }
      if (rolesRes.error) {
        setError(rolesRes.error.message);
        return;
      }

      setExhibition(exhibitionRes.data!);
      setRoles(rolesRes.data!);
      setZones(zonesRes.data || []);
    } catch {
      setError('Failed to load data');
    }

    setIsLoading(false);
  }, [exhibitionId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // User search with debounce
  const searchUsers = useCallback(
    async (query: string) => {
      if (query.length < 3) {
        setSearchResults([]);
        return;
      }

      setIsSearching(true);
      const response = await exhibitionsApi.searchUsers(exhibitionId, query);

      if (response.data) {
        setSearchResults(response.data);
      }
      setIsSearching(false);
    },
    [exhibitionId]
  );

  useEffect(() => {
    if (searchTimeout.current) {
      clearTimeout(searchTimeout.current);
    }

    if (userSearch.length >= 3) {
      searchTimeout.current = setTimeout(() => {
        searchUsers(userSearch);
      }, 300);
    } else {
      setSearchResults([]);
    }

    return () => {
      if (searchTimeout.current) {
        clearTimeout(searchTimeout.current);
      }
    };
  }, [userSearch, searchUsers]);

  // Close search results when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSearchResults(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectUser = (user: UserSearchResult) => {
    setSelectedUser(user);
    setUserSearch(user.full_name || user.email);
    setShowSearchResults(false);
    setSearchResults([]);
  };

  const handleAddRole = async () => {
    if (!selectedUser) {
      showError(t('selectUserRequired'));
      return;
    }

    if (selectedRole === 'PARTNER' && selectedZoneIds.length === 0) {
      showError(t('selectZonesRequired'));
      return;
    }

    setIsSubmitting(true);

    const response = await exhibitionsApi.assignRole(exhibitionId, {
      user_id: selectedUser.id,
      role: selectedRole,
      zone_ids: selectedRole === 'PARTNER' ? selectedZoneIds : undefined,
    });

    if (response.error) {
      showError(response.error.message);
    } else if (response.data) {
      setRoles((prev) => [...prev, response.data!]);
      showSuccess(t('roleAssigned'));
      resetForm();
    }

    setIsSubmitting(false);
  };

  const handleUpdateRole = async () => {
    if (!editingRole) return;

    if (editingRole.role === 'PARTNER' && editZoneIds.length === 0) {
      showError(t('selectZonesRequired'));
      return;
    }

    setIsSubmitting(true);

    const response = await exhibitionsApi.updateRole(exhibitionId, editingRole.id, {
      zone_ids: editZoneIds,
    });

    if (response.error) {
      showError(response.error.message);
    } else if (response.data) {
      setRoles((prev) =>
        prev.map((r) => (r.id === editingRole.id ? response.data! : r))
      );
      showSuccess(t('roleUpdated'));
      setEditingRole(null);
    }

    setIsSubmitting(false);
  };

  const handleDeleteRole = async () => {
    if (!deleteRole) return;

    setIsSubmitting(true);

    const response = await exhibitionsApi.removeRole(exhibitionId, deleteRole.id);

    if (response.error) {
      showError(response.error.message);
    } else {
      setRoles((prev) => prev.filter((r) => r.id !== deleteRole.id));
      showSuccess(t('roleRemoved'));
    }

    setIsSubmitting(false);
    setDeleteRole(null);
  };

  const resetForm = () => {
    setShowAddForm(false);
    setSelectedUser(null);
    setUserSearch('');
    setSelectedRole('ORGANIZER');
    setSelectedZoneIds([]);
    setSearchResults([]);
  };

  const toggleZone = (zoneId: string, setter: (fn: (prev: string[]) => string[]) => void) => {
    setter((prev) =>
      prev.includes(zoneId) ? prev.filter((id) => id !== zoneId) : [...prev, zoneId]
    );
  };

  const getZoneName = (zoneId: string) => {
    const zone = zones.find((z) => z.id === zoneId);
    return zone?.name || zoneId;
  };

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-8 w-64 rounded" style={{ backgroundColor: 'var(--color-bg-secondary)' }} />
        <div className="h-64 rounded-lg" style={{ backgroundColor: 'var(--color-bg-secondary)' }} />
      </div>
    );
  }

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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/admin/exhibitions"
            className="text-sm hover:underline"
            style={{ color: 'var(--color-text-muted)' }}
          >
            &larr; {t('backToExhibitions')}
          </Link>
          <h2
            className="text-xl font-semibold mt-1"
            style={{ color: 'var(--color-text-primary)' }}
          >
            {t('title', { exhibition: exhibition?.title })}
          </h2>
        </div>
        {!showAddForm && (
          <Button onClick={() => setShowAddForm(true)}>{t('addRole')}</Button>
        )}
      </div>

      {/* Add role form */}
      {showAddForm && (
        <Card>
          <Card.Header>
            <Card.Title>{t('assignRole')}</Card.Title>
          </Card.Header>
          <Card.Content className="space-y-4">
            {/* User search */}
            <div ref={searchRef} className="relative">
              <label
                className="block text-sm font-medium mb-1"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('selectUser')}
              </label>
              <Input
                placeholder={t('searchUserPlaceholder')}
                value={userSearch}
                onChange={(e) => {
                  setUserSearch(e.target.value);
                  setSelectedUser(null);
                  setShowSearchResults(true);
                }}
                onFocus={() => setShowSearchResults(true)}
              />
              {/* Search results dropdown */}
              {showSearchResults && (searchResults.length > 0 || isSearching) && (
                <div
                  className="absolute z-10 w-full mt-1 rounded-md shadow-lg max-h-60 overflow-auto"
                  style={{ backgroundColor: 'var(--color-bg-primary)', border: '1px solid var(--color-border)' }}
                >
                  {isSearching ? (
                    <div className="p-3 text-sm" style={{ color: 'var(--color-text-muted)' }}>
                      {t('searching')}
                    </div>
                  ) : (
                    searchResults.map((user) => (
                      <button
                        key={user.id}
                        type="button"
                        className="w-full text-left px-4 py-2 hover:bg-slate-100 dark:hover:bg-slate-800"
                        onClick={() => handleSelectUser(user)}
                      >
                        <div style={{ color: 'var(--color-text-primary)' }}>
                          {user.full_name || user.email}
                        </div>
                        {user.full_name && (
                          <div className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                            {user.email}
                          </div>
                        )}
                      </button>
                    ))
                  )}
                </div>
              )}
              {userSearch.length > 0 && userSearch.length < 3 && (
                <p className="text-xs mt-1" style={{ color: 'var(--color-text-muted)' }}>
                  {t('minChars')}
                </p>
              )}
              {selectedUser && (
                <p className="text-sm mt-1" style={{ color: 'var(--color-text-success)' }}>
                  {t('userSelected', { email: selectedUser.email })}
                </p>
              )}
            </div>

            {/* Role select */}
            <div>
              <label
                className="block text-sm font-medium mb-1"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {t('role')}
              </label>
              <Select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value as ExhibitionRole)}
                options={[
                  { value: 'ORGANIZER', label: tRoles('ORGANIZER') },
                  { value: 'PARTNER', label: tRoles('PARTNER') },
                ]}
              />
            </div>

            {/* Zone selection for PARTNER */}
            {selectedRole === 'PARTNER' && (
              <div>
                <label
                  className="block text-sm font-medium mb-2"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {t('selectZones')}
                </label>
                {zones.length === 0 ? (
                  <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                    {t('noZonesAvailable')}
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {zones.map((zone) => (
                      <button
                        key={zone.id}
                        type="button"
                        onClick={() => toggleZone(zone.id, setSelectedZoneIds)}
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                          selectedZoneIds.includes(zone.id)
                            ? 'bg-ludis-primary text-white'
                            : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        {zone.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <Button onClick={handleAddRole} disabled={isSubmitting || !selectedUser}>
                {isSubmitting ? tCommon('saving') : t('assign')}
              </Button>
              <Button variant="ghost" onClick={resetForm}>
                {tCommon('cancel')}
              </Button>
            </div>
          </Card.Content>
        </Card>
      )}

      {/* Current roles list */}
      <Card>
        <Card.Header>
          <Card.Title>{t('currentRoles')}</Card.Title>
        </Card.Header>
        <Card.Content className="p-0">
          {roles.length === 0 ? (
            <div className="p-6 text-center">
              <p style={{ color: 'var(--color-text-muted)' }}>{t('noRoles')}</p>
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
                      {t('user')}
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
                      {t('zones')}
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
                  {roles.map((role) => (
                    <tr
                      key={role.id}
                      className="border-b last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      style={{ borderColor: 'var(--color-border)' }}
                    >
                      <td className="p-4">
                        <span
                          className="font-medium"
                          style={{ color: 'var(--color-text-primary)' }}
                        >
                          {role.user_full_name || role.user_email}
                        </span>
                        {role.user_full_name && (
                          <span
                            className="block text-sm"
                            style={{ color: 'var(--color-text-muted)' }}
                          >
                            {role.user_email}
                          </span>
                        )}
                      </td>
                      <td className="p-4">
                        <Badge
                          variant={role.role === 'ORGANIZER' ? 'primary' : 'secondary'}
                        >
                          {tRoles(role.role)}
                        </Badge>
                      </td>
                      <td className="p-4">
                        {role.role === 'PARTNER' && role.zone_ids ? (
                          editingRole?.id === role.id ? (
                            <div className="flex flex-wrap gap-2">
                              {zones.map((zone) => (
                                <button
                                  key={zone.id}
                                  type="button"
                                  onClick={() => toggleZone(zone.id, setEditZoneIds)}
                                  className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                                    editZoneIds.includes(zone.id)
                                      ? 'bg-ludis-primary text-white'
                                      : 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300'
                                  }`}
                                >
                                  {zone.name}
                                </button>
                              ))}
                            </div>
                          ) : (
                            <div className="flex flex-wrap gap-1">
                              {role.zone_ids.map((zoneId) => (
                                <Badge key={zoneId} variant="outline">
                                  {getZoneName(zoneId)}
                                </Badge>
                              ))}
                            </div>
                          )
                        ) : (
                          <span style={{ color: 'var(--color-text-muted)' }}>
                            {role.role === 'ORGANIZER' ? t('allZones') : '-'}
                          </span>
                        )}
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex justify-end gap-2">
                          {editingRole?.id === role.id ? (
                            <>
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={handleUpdateRole}
                                disabled={isSubmitting}
                              >
                                {tCommon('save')}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setEditingRole(null)}
                              >
                                {tCommon('cancel')}
                              </Button>
                            </>
                          ) : (
                            <>
                              {role.role === 'PARTNER' && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    setEditingRole(role);
                                    setEditZoneIds(role.zone_ids || []);
                                  }}
                                >
                                  {t('editZones')}
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => setDeleteRole(role)}
                                className="text-red-600 hover:text-red-700"
                              >
                                {t('remove')}
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card.Content>
      </Card>

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        isOpen={!!deleteRole}
        onClose={() => setDeleteRole(null)}
        onConfirm={handleDeleteRole}
        title={t('confirmRemoveTitle')}
        message={t('confirmRemoveMessage', {
          user: deleteRole?.user_full_name || deleteRole?.user_email || '',
          role: deleteRole ? tRoles(deleteRole.role) : '',
        })}
        confirmLabel={t('remove')}
        cancelLabel={tCommon('cancel')}
        isLoading={isSubmitting}
        variant="danger"
      />
    </div>
  );
}
