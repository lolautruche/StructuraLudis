'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslations } from 'next-intl';
import {
  exhibitionsApi,
  zonesApi,
  ExhibitionRoleAssignment,
  ExhibitionRole,
  Zone,
  UserSearchResult,
} from '@/lib/api';
import { Button, Card, Badge, ConfirmDialog, Input, Select } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';

interface RolesListProps {
  exhibitionId: string;
}

export function RolesList({ exhibitionId }: RolesListProps) {
  const t = useTranslations('Admin.roles');
  const tCommon = useTranslations('Common');
  const tRoles = useTranslations('Common.exhibitionRoles');
  const { user: currentUser } = useAuth();

  // Data states
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

  // Load roles and zones
  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      setError(null);

      const [rolesRes, zonesRes] = await Promise.all([
        exhibitionsApi.listRoles(exhibitionId),
        zonesApi.list(exhibitionId),
      ]);

      if (rolesRes.error) {
        setError(rolesRes.error.message);
      } else {
        setRoles(rolesRes.data || []);
      }

      setZones(zonesRes.data || []);
      setIsLoading(false);
    }

    loadData();
  }, [exhibitionId]);

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
      setError(t('selectUserRequired'));
      return;
    }

    if (selectedRole === 'PARTNER' && selectedZoneIds.length === 0) {
      setError(t('selectZonesRequired'));
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const response = await exhibitionsApi.assignRole(exhibitionId, {
      user_id: selectedUser.id,
      role: selectedRole,
      zone_ids: selectedRole === 'PARTNER' ? selectedZoneIds : undefined,
    });

    if (response.error) {
      setError(response.error.message);
    } else if (response.data) {
      setRoles((prev) => [...prev, response.data!]);
      resetForm();
    }

    setIsSubmitting(false);
  };

  const handleUpdateRole = async () => {
    if (!editingRole) return;

    if (editingRole.role === 'PARTNER' && editZoneIds.length === 0) {
      setError(t('selectZonesRequired'));
      return;
    }

    setIsSubmitting(true);
    setError(null);

    const response = await exhibitionsApi.updateRole(exhibitionId, editingRole.id, {
      zone_ids: editZoneIds,
    });

    if (response.error) {
      setError(response.error.message);
    } else if (response.data) {
      setRoles((prev) =>
        prev.map((r) => (r.id === editingRole.id ? response.data! : r))
      );
      setEditingRole(null);
    }

    setIsSubmitting(false);
  };

  const handleDeleteRole = async () => {
    if (!deleteRole) return;

    setIsSubmitting(true);
    setError(null);

    const response = await exhibitionsApi.removeRole(exhibitionId, deleteRole.id);

    if (response.error) {
      setError(response.error.message);
    } else {
      setRoles((prev) => prev.filter((r) => r.id !== deleteRole.id));
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
      <div className="animate-pulse space-y-3">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-16 bg-slate-200 dark:bg-slate-700 rounded"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Add button */}
      {!showAddForm && (
        <div className="flex justify-end">
          <Button variant="primary" onClick={() => setShowAddForm(true)}>
            {t('addRole')}
          </Button>
        </div>
      )}

      {/* Add role form */}
      {showAddForm && (
        <Card>
          <Card.Content className="space-y-4">
            <h4
              className="text-lg font-medium"
              style={{ color: 'var(--color-text-primary)' }}
            >
              {t('assignRole')}
            </h4>

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
      {roles.length === 0 && !showAddForm ? (
        <div
          className="text-center py-8"
          style={{ color: 'var(--color-text-muted)' }}
        >
          {t('noRoles')}
        </div>
      ) : (
        <div className="space-y-2">
          {roles.map((role) => (
            <div
              key={role.id}
              className="flex items-center justify-between p-4 border rounded-lg"
              style={{ borderColor: 'var(--color-border)' }}
            >
              <div className="flex items-center gap-4">
                <div>
                  <div
                    className="font-medium"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    {role.user_full_name || role.user_email}
                  </div>
                  {role.user_full_name && (
                    <div
                      className="text-sm"
                      style={{ color: 'var(--color-text-muted)' }}
                    >
                      {role.user_email}
                    </div>
                  )}
                </div>
                <Badge variant={role.role === 'ORGANIZER' ? 'primary' : 'secondary'}>
                  {tRoles(role.role)}
                </Badge>
                {role.is_main_organizer && (
                  <Badge variant="outline" size="sm">
                    {t('mainOrganizer')}
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-4">
                {/* Zones for PARTNER */}
                {role.role === 'PARTNER' && (
                  <div className="flex flex-wrap gap-1">
                    {editingRole?.id === role.id ? (
                      zones.map((zone) => (
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
                      ))
                    ) : (
                      role.zone_ids?.map((zoneId) => (
                        <Badge key={zoneId} variant="outline" size="sm">
                          {getZoneName(zoneId)}
                        </Badge>
                      ))
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-2">
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
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setEditingRole(role);
                            setEditZoneIds(role.zone_ids || []);
                          }}
                        >
                          {tCommon('edit')}
                        </Button>
                      )}
                      {/* Can remove if: not main organizer AND not yourself */}
                      {!role.is_main_organizer && role.user_id !== currentUser?.id && (
                        <Button
                          variant="danger"
                          size="sm"
                          onClick={() => setDeleteRole(role)}
                        >
                          {t('remove')}
                        </Button>
                      )}
                      {/* Show message for own role (not main organizer) */}
                      {!role.is_main_organizer && role.user_id === currentUser?.id && (
                        <span
                          className="text-xs italic"
                          style={{ color: 'var(--color-text-muted)' }}
                        >
                          {t('cannotRemoveSelf')}
                        </span>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete confirmation */}
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
