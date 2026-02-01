# Roadmap & Priorities

Ce document trace les décisions de priorisation et l'état d'avancement du projet.
**Dernière mise à jour**: 2026-01-31

---

## Priorités actuelles

### En cours

| Issue | Titre | Job Stories | Statut |
|-------|-------|-------------|--------|
| [#73](https://github.com/lolautruche/StructuraLudis/issues/73) | Email verification on registration | JS.E1 (Privacy/Consent) | Plan validé, implémentation à faire |

### Prochaines priorités (MVP)

| Issue | Titre | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#60](https://github.com/lolautruche/StructuraLudis/issues/60) | User Settings & Profile Page | JS.X2, JS.E2, JS.E5 | Profil, préférences, GDPR basics |
| [#62](https://github.com/lolautruche/StructuraLudis/issues/62) | Notification Center & Bell | JS.C2, JS.C3 | Notifications in-app |
| [#8](https://github.com/lolautruche/StructuraLudis/issues/8) | Proposer: Session Submission Form | JS.B1-B5 | Formulaire de soumission (partiellement fait) |
| [#7](https://github.com/lolautruche/StructuraLudis/issues/7) | Admin: Event Configuration | JS.A2, JS.A3, JS.A5 | Config slots/zones admin |

### Post-MVP

| Issue | Titre | Job Stories | Notes |
|-------|-------|-------------|-------|
| [#74](https://github.com/lolautruche/StructuraLudis/issues/74) | Magic link authentication | JS.X1 variant | Passwordless login |
| [#75](https://github.com/lolautruche/StructuraLudis/issues/75) | Persist theme preference | JS.X2 | Préférence thème en BDD |
| [#70](https://github.com/lolautruche/StructuraLudis/issues/70) | Waitlist configuration | JS.A9 | Config waitlist par event |
| [#55](https://github.com/lolautruche/StructuraLudis/issues/55) | External Game Database Sync | JS.05 | Import GROG/BGG |
| [#56](https://github.com/lolautruche/StructuraLudis/issues/56) | Game Autocomplete & Metadata | JS.B3, JS.B9 | Enrichir les métadonnées jeux |
| [#13](https://github.com/lolautruche/StructuraLudis/issues/13) | SuperAdmin Portal | JS.01-04 | Admin globale |
| [#10](https://github.com/lolautruche/StructuraLudis/issues/10) | Partner Zone Management | JS.D1 | Gestion zones partenaires |

### GDPR (à planifier)

| Issue | Titre | Job Stories |
|-------|-------|-------------|
| [#48](https://github.com/lolautruche/StructuraLudis/issues/48) | Data Access (Right of Access) | JS.E2 |
| [#49](https://github.com/lolautruche/StructuraLudis/issues/49) | Account Deletion | JS.E3 |
| [#50](https://github.com/lolautruche/StructuraLudis/issues/50) | Data Portability | JS.E4 |
| [#51](https://github.com/lolautruche/StructuraLudis/issues/51) | Consent Management | JS.E5 |
| [#52](https://github.com/lolautruche/StructuraLudis/issues/52) | Data Retention Transparency | JS.E6 |
| [#53](https://github.com/lolautruche/StructuraLudis/issues/53) | GDPR Request Management | JS.E7 |
| [#54](https://github.com/lolautruche/StructuraLudis/issues/54) | Data Anonymization | JS.E8 |

---

## Travail terminé récemment

| Issue | Titre | Job Stories | Date |
|-------|-------|-------------|------|
| [#61](https://github.com/lolautruche/StructuraLudis/issues/61) | Session Detail & Booking Flow | JS.C1, JS.C2, JS.C4, JS.C8, JS.C9 | 2026-01-31 |
| [#69](https://github.com/lolautruche/StructuraLudis/issues/69) | Light theme option | - | 2026-01-31 |
| [#59](https://github.com/lolautruche/StructuraLudis/issues/59) | Authentication Pages | JS.X1 | 2026-01-30 |
| [#58](https://github.com/lolautruche/StructuraLudis/issues/58) | Frontend Foundation | - | 2026-01-29 |
| [#47](https://github.com/lolautruche/StructuraLudis/issues/47) | Privacy Policy Consent | JS.E1 | 2026-01-28 |

---

## Décisions de conception

### Vérification email (#73)
- **Décision**: Ne pas bloquer le login, mais bloquer les réservations si email non vérifié
- **Rate limiting**: Cooldown de 60s via `email_verification_sent_at`
- **Expiration token**: 7 jours
- **Plan détaillé**: `~/.claude/plans/glimmering-puzzling-spring.md`

### Architecture frontend
- Next.js 14 avec App Router
- next-intl pour l'i18n (FR/EN)
- Tailwind CSS + composants UI custom
- API client avec fetch wrapper

### Architecture backend
- FastAPI + SQLAlchemy async
- PostgreSQL
- Alembic pour les migrations
- Templates email Jinja2 avec i18n

---

## Référence Job Stories

Les Job Stories sont définies dans [PRD.md](./PRD.md).

### Légende des EPICs
- **EPIC 0**: Administration globale (Super Admin)
- **EPIC A**: Configuration organisateur
- **EPIC B**: Parcours proposeur (MJ)
- **EPIC C**: Expérience joueur
- **EPIC D**: Gestion partenaires
- **EPIC E**: GDPR & Privacy
- **Cross-cutting**: Auth, profil, notifications
