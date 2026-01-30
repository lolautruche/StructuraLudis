'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Button, Card } from '@/components/ui';

export default function HomePage() {
  const t = useTranslations('Discovery');
  const tCommon = useTranslations('Common');

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          <span className="text-gradient">Structura Ludis</span>
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-8">
          Organisez et rejoignez des sessions de jeux de rôle facilement.
          Trouvez votre prochaine partie en quelques clics.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link href="/sessions">
            <Button variant="primary" size="lg">
              {t('title')}
            </Button>
          </Link>
          <Link href="/auth/register">
            <Button variant="secondary" size="lg">
              {tCommon('register')}
            </Button>
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid md:grid-cols-3 gap-6">
        <Card>
          <Card.Content className="text-center py-8">
            <div className="text-4xl mb-4">🎲</div>
            <h3 className="text-lg font-semibold mb-2">Découvrez des parties</h3>
            <p className="text-slate-400 text-sm">
              Explorez les sessions disponibles et trouvez le jeu qui vous correspond.
            </p>
          </Card.Content>
        </Card>

        <Card>
          <Card.Content className="text-center py-8">
            <div className="text-4xl mb-4">📅</div>
            <h3 className="text-lg font-semibold mb-2">Réservez facilement</h3>
            <p className="text-slate-400 text-sm">
              Inscrivez-vous en un clic et recevez vos confirmations par email.
            </p>
          </Card.Content>
        </Card>

        <Card>
          <Card.Content className="text-center py-8">
            <div className="text-4xl mb-4">🔔</div>
            <h3 className="text-lg font-semibold mb-2">Restez informé</h3>
            <p className="text-slate-400 text-sm">
              Notifications en temps réel pour les changements et rappels.
            </p>
          </Card.Content>
        </Card>
      </section>
    </div>
  );
}
