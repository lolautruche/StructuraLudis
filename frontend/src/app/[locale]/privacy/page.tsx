'use client';

import { useTranslations } from 'next-intl';
import { Link } from '@/i18n/routing';
import { Card, Button } from '@/components/ui';

export default function PrivacyPolicyPage() {
  const t = useTranslations('Privacy');

  return (
    <div className="max-w-3xl mx-auto">
      <Card>
        <Card.Header>
          <Card.Title className="text-2xl">{t('title')}</Card.Title>
          <Card.Description>{t('lastUpdated')}</Card.Description>
        </Card.Header>
        <Card.Content className="prose prose-invert prose-slate max-w-none">
          <section className="space-y-4">
            <h2 className="text-lg font-semibold text-white">{t('section1Title')}</h2>
            <p className="text-slate-300">{t('section1Content')}</p>
          </section>

          <section className="space-y-4 mt-8">
            <h2 className="text-lg font-semibold text-white">{t('section2Title')}</h2>
            <p className="text-slate-300">{t('section2Content')}</p>
            <ul className="list-disc list-inside text-slate-300 space-y-1">
              <li>{t('dataCollected1')}</li>
              <li>{t('dataCollected2')}</li>
              <li>{t('dataCollected3')}</li>
              <li>{t('dataCollected4')}</li>
            </ul>
          </section>

          <section className="space-y-4 mt-8">
            <h2 className="text-lg font-semibold text-white">{t('section3Title')}</h2>
            <p className="text-slate-300">{t('section3Content')}</p>
          </section>

          <section className="space-y-4 mt-8">
            <h2 className="text-lg font-semibold text-white">{t('section4Title')}</h2>
            <p className="text-slate-300">{t('section4Content')}</p>
            <ul className="list-disc list-inside text-slate-300 space-y-1">
              <li>{t('rights1')}</li>
              <li>{t('rights2')}</li>
              <li>{t('rights3')}</li>
              <li>{t('rights4')}</li>
            </ul>
          </section>

          <section className="space-y-4 mt-8">
            <h2 className="text-lg font-semibold text-white">{t('section5Title')}</h2>
            <p className="text-slate-300">{t('section5Content')}</p>
          </section>
        </Card.Content>
        <Card.Footer className="flex justify-between items-center print:hidden">
          <Link href="/auth/register">
            <Button variant="ghost">← {t('back')}</Button>
          </Link>
          <Button variant="secondary" onClick={() => window.print()}>
            {t('print')}
          </Button>
        </Card.Footer>
      </Card>
    </div>
  );
}
